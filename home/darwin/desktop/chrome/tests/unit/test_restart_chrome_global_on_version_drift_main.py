import argparse

import drift_observation_state
import restart_chrome_global_on_version_drift as entrypoint

ON_DISK_VERSION = "149.0.7827.197"
DRIFTED_RUNNING_VERSIONS = {"149.0.7827.156"}


def configure_main(
    monkeypatch,
    tmp_path,
    *,
    on_disk_version=ON_DISK_VERSION,
    processes=("chrome-global-main",),
    running_framework_versions=DRIFTED_RUNNING_VERSIONS,
    chrome_is_frontmost=False,
    restart_succeeds=True,
):
    state_file_path = tmp_path / "state.json"
    restart_calls = []

    monkeypatch.setattr(
        entrypoint, "DRIFT_OBSERVATION_STATE_FILE_PATH", state_file_path
    )
    monkeypatch.setattr(
        entrypoint,
        "parse_command_line_arguments",
        lambda: argparse.Namespace(launcher_binary="/launcher"),
    )
    monkeypatch.setattr(
        entrypoint, "read_on_disk_chrome_version", lambda: on_disk_version
    )
    monkeypatch.setattr(
        entrypoint, "find_chrome_global_processes", lambda: list(processes)
    )
    monkeypatch.setattr(
        entrypoint,
        "collect_running_framework_versions",
        lambda found_processes: set(running_framework_versions),
    )
    monkeypatch.setattr(
        entrypoint, "chrome_is_the_frontmost_application", lambda: chrome_is_frontmost
    )

    def fake_restart(launcher_binary, on_disk, running_versions):
        restart_calls.append((launcher_binary, on_disk, running_versions))
        return restart_succeeds

    monkeypatch.setattr(entrypoint, "restart_chrome_global", fake_restart)
    return state_file_path, restart_calls


def test_missing_on_disk_version_returns_without_writing(monkeypatch, tmp_path):
    state_file_path, restart_calls = configure_main(
        monkeypatch, tmp_path, on_disk_version=None
    )
    entrypoint.main()
    assert not state_file_path.exists()
    assert restart_calls == []


def test_no_processes_resets_count(monkeypatch, tmp_path):
    state_file_path, restart_calls = configure_main(monkeypatch, tmp_path, processes=())
    drift_observation_state.write_consecutive_drift_observation_count(
        state_file_path, 1
    )
    entrypoint.main()
    assert (
        drift_observation_state.read_consecutive_drift_observation_count(
            state_file_path
        )
        == 0
    )
    assert restart_calls == []


def test_running_matches_on_disk_resets_count(monkeypatch, tmp_path):
    state_file_path, restart_calls = configure_main(
        monkeypatch, tmp_path, running_framework_versions={ON_DISK_VERSION}
    )
    drift_observation_state.write_consecutive_drift_observation_count(
        state_file_path, 1
    )
    entrypoint.main()
    assert (
        drift_observation_state.read_consecutive_drift_observation_count(
            state_file_path
        )
        == 0
    )
    assert restart_calls == []


def test_drift_while_frontmost_defers_and_leaves_count(monkeypatch, tmp_path):
    state_file_path, restart_calls = configure_main(
        monkeypatch, tmp_path, chrome_is_frontmost=True
    )
    drift_observation_state.write_consecutive_drift_observation_count(
        state_file_path, 1
    )
    entrypoint.main()
    assert (
        drift_observation_state.read_consecutive_drift_observation_count(
            state_file_path
        )
        == 1
    )
    assert restart_calls == []


def test_first_non_frontmost_drift_increments_without_restart(monkeypatch, tmp_path):
    state_file_path, restart_calls = configure_main(monkeypatch, tmp_path)
    entrypoint.main()
    assert (
        drift_observation_state.read_consecutive_drift_observation_count(
            state_file_path
        )
        == 1
    )
    assert restart_calls == []


def test_second_non_frontmost_drift_restarts_then_resets(monkeypatch, tmp_path):
    state_file_path, restart_calls = configure_main(monkeypatch, tmp_path)
    drift_observation_state.write_consecutive_drift_observation_count(
        state_file_path, 1
    )
    entrypoint.main()
    assert (
        drift_observation_state.read_consecutive_drift_observation_count(
            state_file_path
        )
        == 0
    )
    assert restart_calls == [("/launcher", ON_DISK_VERSION, DRIFTED_RUNNING_VERSIONS)]


def test_failed_restart_persists_count_for_retry(monkeypatch, tmp_path):
    state_file_path, restart_calls = configure_main(
        monkeypatch, tmp_path, restart_succeeds=False
    )
    drift_observation_state.write_consecutive_drift_observation_count(
        state_file_path, 1
    )
    entrypoint.main()
    assert (
        drift_observation_state.read_consecutive_drift_observation_count(
            state_file_path
        )
        == 2
    )
    assert len(restart_calls) == 1
