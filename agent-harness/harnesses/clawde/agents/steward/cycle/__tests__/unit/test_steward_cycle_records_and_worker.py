import json
from pathlib import Path

from cycle_commands import CommandResult
from cycle_configuration import CycleConfiguration
from cycle_observation import settled_activation, settled_validation
from cycle_validation_worker import built_toplevel, validate_revision, verdict_for

REVISION = "a" * 40


def configuration_in(
    state_directory: Path, dry_run: bool = False
) -> CycleConfiguration:
    return CycleConfiguration(
        repository=Path("/home/user/.dotfiles"),
        entrypoint=Path("/home/user/entrypoint"),
        configuration_attribute="nixosConfigurations.host.config.system.build.toplevel",
        state_directory=state_directory,
        idle_marker=state_directory / "idle",
        inbox_directory=state_directory / "inbox",
        peers_file=state_directory / "peers.json",
        nix_binary="/run/current-system/sw/bin/nix",
        rebuild_command="rebuild",
        dry_run=dry_run,
    )


class EntrypointRunner:
    def run(self, arguments, directory, timeout_seconds):
        if "rev-parse" in arguments:
            return CommandResult(0, "e" * 40 + "\n")
        return CommandResult(0, "")


def test_pinned_references_name_the_exact_revision_and_the_entrypoint():
    configuration = configuration_in(Path("/state"))

    assert configuration.pinned_repository_reference(REVISION) == (
        f"git+file:///home/user/.dotfiles?submodules=1&rev={REVISION}"
    )
    assert configuration.entrypoint_installable("e" * 40) == (
        f"git+file:///home/user/entrypoint?rev={'e' * 40}"
        "#nixosConfigurations.host.config.system.build.toplevel"
    )


def test_verdicts_separate_breakage_from_infrastructure_noise():
    assert verdict_for(0, "/nix/store/system", "") == "green"
    assert verdict_for(0, "", "") == "red"
    assert verdict_for(1, "", "error: attribute 'missing' missing") == "red"
    assert (
        verdict_for(1, "", "error: unable to download 'https://cache'") == "transient"
    )
    assert verdict_for(124, "", "") == "transient"


def test_built_toplevel_is_the_last_store_path_printed():
    assert (
        built_toplevel("warning: dirty\n/nix/store/aaa-system\n")
        == "/nix/store/aaa-system"
    )
    assert built_toplevel("") == ""


def test_worker_records_a_green_verdict_and_the_last_green_revision(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    configuration = configuration_in(tmp_path)
    captured = {}

    def build(arguments, directory, log_path):
        captured["arguments"] = arguments
        captured["directory"] = directory
        log_path.write_text("building\n")
        return 0, "/nix/store/new-system\n"

    record = validate_revision(
        configuration, EntrypointRunner(), REVISION, 2, build=build
    )

    stored = json.loads((tmp_path / "validations" / f"{REVISION}.json").read_text())
    assert stored == record
    assert record["status"] == "green"
    assert record["toplevel"] == "/nix/store/new-system"
    assert record["attempt"] == 2
    assert record["entrypoint_head"] == "e" * 40
    assert captured["directory"] == tmp_path
    assert configuration.pinned_repository_reference(REVISION) in captured["arguments"]
    assert configuration.entrypoint_installable("e" * 40) in captured["arguments"]
    assert (tmp_path / "last-green-revision").read_text().strip() == REVISION


def test_worker_red_verdict_leaves_the_last_green_revision_alone(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "last-green-revision").write_text("g" * 40 + "\n")

    def build(arguments, directory, log_path):
        log_path.write_text("error: infinite recursion encountered\n")
        return 1, ""

    record = validate_revision(
        configuration_in(tmp_path), EntrypointRunner(), REVISION, 1, build=build
    )

    assert record["status"] == "red"
    assert (tmp_path / "last-green-revision").read_text().strip() == "g" * 40


def test_a_running_validation_without_its_scope_counts_as_transient():
    record = {"status": "running", "attempt": 1}

    assert settled_validation(record, ())["status"] == "transient"
    assert settled_validation(record, ("steward-validate-aaaaaaaa.scope",)) is record


def test_a_finished_activation_is_judged_by_the_live_system():
    record = {"status": "running", "toplevel": "/nix/store/validated"}

    assert (
        settled_activation(record, (), "/nix/store/validated")["status"] == "activated"
    )
    assert settled_activation(record, (), "/nix/store/other")["status"] == "failed"
    assert (
        settled_activation(
            record, ("steward-activation-aaaaaaaa.scope",), "/nix/store/other"
        )
        is record
    )


def test_settings_place_the_idle_marker_in_the_runtime_directory(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps(
            {
                "repository": "/home/user/.dotfiles",
                "entrypoint": "/home/user/entrypoint",
                "configuration_attribute": "nixosConfigurations.host.config.system.build.toplevel",
                "state_directory": "/home/user/state",
                "idle_marker_name": "operator-idle",
                "inbox_directory": "/home/user/inbox",
                "peers_file": "/home/user/peers.json",
                "nix_binary": "/run/current-system/sw/bin/nix",
                "rebuild_command": "/nix/store/aaa-rebuild/bin/rebuild",
            }
        )
    )

    configuration = CycleConfiguration.from_settings(
        settings, Path("/run/user/1000"), dry_run=True
    )

    assert configuration.idle_marker == Path("/run/user/1000/operator-idle")
    assert configuration.dry_run
    assert configuration.lock_file == Path("/home/user/state/cycle.lock")
