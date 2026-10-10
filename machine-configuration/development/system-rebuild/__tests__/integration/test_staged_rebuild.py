import json
import subprocess
import pytest

from staged_rebuild_support import (
    SCRIPTS,
    SYSTEM_PATH,
    build_staged_environment,
    read_events,
    write_prepared_request,
)


def run_staged(environment, action, request):
    return subprocess.run(
        [str(SCRIPTS / "staged-rebuild"), action, str(request)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
    )


@pytest.mark.parametrize("action", ["switch", "boot"])
def test_staged_clients_exit_before_realization_and_use_native_activation(
    managed_rebuild_environment, tmp_path, action
):
    environment = build_staged_environment(managed_rebuild_environment, tmp_path)
    request = write_prepared_request(tmp_path, action, ["--option", "cores", "2"])
    completed = run_staged(environment, action, request)
    assert completed.returncode == 0, completed.stderr
    events = [
        event
        for event in read_events(tmp_path)
        if "--realise" not in event["arguments"]
        or event["arguments"][event["arguments"].index("--realise") + 1].endswith(
            ".drv"
        )
    ]
    assert len(events) == 2
    assert "eval" in events[0]["arguments"]
    assert "--realise" in events[1]["arguments"]
    assert events[0]["pid"] != events[1]["pid"]
    assert all(event["gc"] == ["67108864", "8"] for event in events)
    assert "--offline" in events[0]["arguments"]
    assert "allow-import-from-derivation" not in events[0]["arguments"]
    activation = read_events(tmp_path, "native-events")
    assert [event["phase"] for event in activation] == ["profile", "activate"]
    assert activation[1]["action"] == action
    assert activation[1]["system"] == SYSTEM_PATH
    assert "phase=evaluation" in completed.stderr
    assert "phase=realization" in completed.stderr
    assert "phase=activation" in completed.stderr
    assert "peak_rss_kib=" in completed.stderr
    assert "--store-path" not in completed.stdout + completed.stderr


@pytest.mark.parametrize("failed_phase", ["EVAL", "REALISE"])
def test_failed_client_preserves_status_and_cannot_activate(
    managed_rebuild_environment, tmp_path, failed_phase
):
    environment = build_staged_environment(managed_rebuild_environment, tmp_path)
    environment[f"TEST_{failed_phase}_FAILURE"] = "42"
    completed = run_staged(environment, "switch", write_prepared_request(tmp_path))
    assert completed.returncode == 42, completed.stderr
    assert not read_events(tmp_path, "native-events")
    assert len(read_events(tmp_path)) == (2 if failed_phase == "EVAL" else 3)


def test_boot_specialisation_is_rejected_before_evaluation(
    managed_rebuild_environment, tmp_path
):
    environment = build_staged_environment(managed_rebuild_environment, tmp_path)
    request = write_prepared_request(tmp_path, "boot", ["--specialisation", "desktop"])
    completed = run_staged(environment, "boot", request)
    assert completed.returncode != 0
    assert not read_events(tmp_path)
    assert not read_events(tmp_path, "native-events")


def test_native_validity_check_prevents_profile_change(
    managed_rebuild_environment, tmp_path
):
    environment = build_staged_environment(managed_rebuild_environment, tmp_path)
    environment["TEST_INVALID_SYSTEM"] = "1"
    completed = run_staged(environment, "switch", write_prepared_request(tmp_path))
    assert completed.returncode != 0
    assert "native validity check failed" in completed.stderr
    assert not read_events(tmp_path, "native-events")


def test_prepared_action_mismatch_fails_before_any_client(
    managed_rebuild_environment, tmp_path
):
    environment = build_staged_environment(managed_rebuild_environment, tmp_path)
    completed = run_staged(
        environment, "boot", write_prepared_request(tmp_path, "switch")
    )
    assert completed.returncode != 0
    assert not read_events(tmp_path)


def test_request_mutation_during_evaluation_cannot_turn_boot_into_live_activation(
    managed_rebuild_environment, tmp_path
):
    environment = build_staged_environment(managed_rebuild_environment, tmp_path)
    request = write_prepared_request(tmp_path, "boot")
    environment["TEST_REWRITE_REQUEST"] = str(request)
    completed = run_staged(environment, "boot", request)
    assert completed.returncode == 0, completed.stderr
    activation = read_events(tmp_path, "native-events")
    assert activation[-1]["action"] == "boot"


@pytest.mark.parametrize("missing_source", [0, 1])
def test_source_manifest_omission_fails_before_any_privileged_client(
    managed_rebuild_environment, tmp_path, missing_source
):
    environment = build_staged_environment(managed_rebuild_environment, tmp_path)
    request = write_prepared_request(tmp_path)
    prepared = json.loads(request.read_text())
    prepared["sources"].pop(missing_source)
    request.write_text(json.dumps(prepared))
    completed = run_staged(environment, "switch", request)
    assert completed.returncode == 1
    assert "not prefetched" in completed.stderr
    assert not read_events(tmp_path)


@pytest.mark.parametrize("failed_phase", ["PROFILE", "ACTIVATION"])
def test_native_library_failure_preserves_status_and_stops_later_phases(
    managed_rebuild_environment, tmp_path, failed_phase
):
    environment = build_staged_environment(managed_rebuild_environment, tmp_path)
    environment[f"TEST_{failed_phase}_FAILURE"] = "42"
    completed = run_staged(environment, "switch", write_prepared_request(tmp_path))
    assert completed.returncode == 42, completed.stderr
    expected = [] if failed_phase == "PROFILE" else ["profile"]
    assert [
        event["phase"] for event in read_events(tmp_path, "native-events")
    ] == expected


def test_switch_preserves_native_profile_specialisation_and_bootloader_options(
    managed_rebuild_environment, tmp_path
):
    environment = build_staged_environment(managed_rebuild_environment, tmp_path)
    request = write_prepared_request(
        tmp_path,
        "switch",
        [
            "--profile-name",
            "custom",
            "--specialisation",
            "desktop",
            "--install-bootloader",
        ],
    )
    completed = run_staged(environment, "switch", request)
    assert completed.returncode == 0, completed.stderr
    native = read_events(tmp_path, "native-events")
    assert native[0]["profile"] == "custom"
    assert native[1]["specialisation"] == "desktop"
    assert native[1]["install_bootloader"] is True
