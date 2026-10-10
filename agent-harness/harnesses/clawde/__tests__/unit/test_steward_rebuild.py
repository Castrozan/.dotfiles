import fcntl
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import steward_rebuild

CONFIGURATION = (
    "git+file:///dotfiles?submodules=1#darwinConfigurations.rin.system.outPath"
)


@pytest.fixture(autouse=True)
def rebuild_guard_environment(monkeypatch):
    monkeypatch.setenv("SYSTEM_REBUILD_LOCK_GUARD", "fixture-rebuild-guard")


def test_launch_detaches_with_an_inherited_lock_and_persistent_output(
    tmp_path, monkeypatch
):
    launches = []

    def launch(arguments, **options):
        launches.append((arguments, options))
        assert not options["stdout"].closed
        assert len(options["pass_fds"]) == 1
        return SimpleNamespace(pid=413)

    monkeypatch.setattr(subprocess, "Popen", launch)

    assert steward_rebuild.launch_rebuild(tmp_path, CONFIGURATION) == 413

    arguments, options = launches[0]
    assert arguments[1] == str(Path(steward_rebuild.__file__).resolve())
    assert arguments[2:] == [
        "--worker",
        "--state-directory",
        str(tmp_path),
        "--configuration",
        CONFIGURATION,
    ]
    assert options["start_new_session"] is True
    assert options["stdin"] == subprocess.DEVNULL
    assert options["stderr"] == subprocess.STDOUT
    assert options["cwd"] == tmp_path


def test_an_active_rebuild_is_not_launched_again(tmp_path, monkeypatch):
    def unexpected_launch(*arguments, **options):
        pytest.fail("an active rebuild must keep its worker and log")

    monkeypatch.setattr(subprocess, "Popen", unexpected_launch)
    log = tmp_path / "rebuild.log"
    log.write_text("existing rebuild output")
    with (tmp_path / "rebuild.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert steward_rebuild.launch_rebuild(tmp_path, CONFIGURATION) is None
    assert log.read_text() == "existing rebuild output"


@pytest.mark.parametrize("exit_code", [0, 1, 42])
def test_worker_records_the_actual_rebuild_outcome(tmp_path, monkeypatch, exit_code):
    calls = []
    closures = iter(["/nix/store/old-system", "/nix/store/new-system"])
    monkeypatch.setattr(steward_rebuild, "current_system", lambda: next(closures))

    def rebuild(arguments, **options):
        if arguments[0] == "fixture-rebuild-guard":
            assert options["timeout"] == 180
            assert "--no-write-lock-file" in arguments
            return SimpleNamespace(
                returncode=0, stdout="/nix/store/new-system", stderr=""
            )
        calls.append(arguments)
        running = json.loads((tmp_path / "rebuild-result.json").read_text())
        assert running["status"] == "running"
        return SimpleNamespace(returncode=exit_code)

    monkeypatch.setattr(subprocess, "run", rebuild)

    assert steward_rebuild.run_rebuild(tmp_path, CONFIGURATION) == exit_code

    result = json.loads((tmp_path / "rebuild-result.json").read_text())
    assert calls == [["rebuild"]]
    assert result["status"] == ("succeeded" if exit_code == 0 else "failed")
    assert result["exit_code"] == exit_code
    assert result["system_before"] == "/nix/store/old-system"
    assert result["system_after"] == "/nix/store/new-system"
    assert result["completed_at"] >= result["started_at"]


def test_a_missing_rebuild_command_records_a_failure(tmp_path, monkeypatch):
    def missing_command(arguments, **options):
        if arguments[0] == "fixture-rebuild-guard":
            return SimpleNamespace(
                returncode=0, stdout="/nix/store/new-system", stderr=""
            )
        raise FileNotFoundError("rebuild is unavailable")

    monkeypatch.setattr(subprocess, "run", missing_command)
    monkeypatch.setattr(steward_rebuild, "current_system", lambda: None)

    assert steward_rebuild.run_rebuild(tmp_path, CONFIGURATION) == 1

    result = json.loads((tmp_path / "rebuild-result.json").read_text())
    assert result["status"] == "failed"
    assert result["error"] == "rebuild is unavailable"


def test_an_unchanged_configuration_does_not_rebuild(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        steward_rebuild, "current_system", lambda: "/nix/store/same-system"
    )

    def evaluate(arguments, **options):
        calls.append(arguments)
        return SimpleNamespace(returncode=0, stdout="/nix/store/same-system", stderr="")

    monkeypatch.setattr(subprocess, "run", evaluate)
    assert steward_rebuild.run_rebuild(tmp_path, CONFIGURATION) == 0
    assert len(calls) == 1
    assert calls[0][:3] == ["fixture-rebuild-guard", "nix", "eval"]
    assert (
        json.loads((tmp_path / "rebuild-result.json").read_text())["status"]
        == "unchanged"
    )


def test_a_switch_to_a_different_closure_cannot_claim_success(tmp_path, monkeypatch):
    monkeypatch.setattr(
        steward_rebuild, "current_system", lambda: "/nix/store/old-system"
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *arguments, **options: SimpleNamespace(
            returncode=0, stdout="/nix/store/wanted-system", stderr=""
        ),
    )

    assert steward_rebuild.run_rebuild(tmp_path, CONFIGURATION) == 1
    result = json.loads((tmp_path / "rebuild-result.json").read_text())
    assert result["status"] == "failed"
    assert result["system_after"] != result["desired_system"]


def test_a_failed_evaluation_does_not_activate(tmp_path, monkeypatch):
    calls = []

    def evaluate(arguments, **options):
        calls.append(arguments)
        return SimpleNamespace(returncode=1, stdout="", stderr="evaluation failed")

    monkeypatch.setattr(subprocess, "run", evaluate)
    monkeypatch.setattr(steward_rebuild, "current_system", lambda: None)
    assert steward_rebuild.run_rebuild(tmp_path, CONFIGURATION) == 1
    assert len(calls) == 1
    result = json.loads((tmp_path / "rebuild-result.json").read_text())
    assert result["status"] == "failed"
    assert "evaluation failed" in result["error"]


def test_evaluation_timeout_records_a_failure(tmp_path, monkeypatch):
    def timed_out(arguments, **options):
        raise subprocess.TimeoutExpired(arguments, options["timeout"])

    monkeypatch.setattr(subprocess, "run", timed_out)
    monkeypatch.setattr(steward_rebuild, "current_system", lambda: None)
    assert steward_rebuild.run_rebuild(tmp_path, CONFIGURATION) == 1
    result = json.loads((tmp_path / "rebuild-result.json").read_text())
    assert result["status"] == "failed"
    assert "180" in result["error"]


@pytest.mark.parametrize(
    "evaluation_output", ["", "not-a-store-path", "/nix/store/one\n/nix/store/two"]
)
def test_invalid_evaluation_output_prevents_activation(
    tmp_path, monkeypatch, evaluation_output
):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *arguments, **options: SimpleNamespace(
            returncode=0, stdout=evaluation_output, stderr=""
        ),
    )
    monkeypatch.setattr(steward_rebuild, "current_system", lambda: None)
    assert steward_rebuild.run_rebuild(tmp_path, CONFIGURATION) == 1
    result = json.loads((tmp_path / "rebuild-result.json").read_text())
    assert result["status"] == "failed"
    assert "system store path" in result["error"]
