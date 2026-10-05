import plistlib
import stat
import subprocess
from types import SimpleNamespace

import pytest

import restart_agenix_launch_agent


@pytest.fixture
def launch_agent(tmp_path):
    plist_path = (
        tmp_path / "Library/LaunchAgents/org.nix-community.home.activate-agenix.plist"
    )
    plist_path.parent.mkdir(parents=True)
    configuration = {
        "KeepAlive": {"Crashed": False, "SuccessfulExit": False},
        "RunAtLoad": True,
        "ProgramArguments": ["/bin/sh", "mount-secrets"],
    }
    plist_path.write_bytes(plistlib.dumps(configuration))
    plist_path.chmod(0o444)
    return plist_path


@pytest.fixture
def clock(monkeypatch):
    state = SimpleNamespace(seconds=0.0)
    monkeypatch.setattr(
        restart_agenix_launch_agent.time, "monotonic", lambda: state.seconds
    )

    def sleep(seconds):
        state.seconds += seconds

    monkeypatch.setattr(restart_agenix_launch_agent.time, "sleep", sleep)
    return state


def test_restart_waits_for_removal_before_cleanup_and_retries_bootstrap(
    tmp_path, monkeypatch, launch_agent, clock
):
    temporary_root = tmp_path / "temporary"
    live_generation = temporary_root / "agenix.d/28"
    live_generation.mkdir(parents=True)
    (live_generation / "token").write_text("live-secret")
    (temporary_root / "agenix").symlink_to(live_generation)
    abandoned_generation = temporary_root / "agenix.d/29"
    abandoned_generation.mkdir()
    incomplete_secret = abandoned_generation / "token.tmp"
    incomplete_secret.write_text("incomplete-secret")
    incomplete_secret.chmod(0o400)
    abandoned_generation.chmod(0o500)
    removal_results = iter([0, 0, 1])
    bootstrap_results = iter([5, 0])
    calls = []

    def run(command, **options):
        calls.append(command)
        if command[1] == "print":
            assert abandoned_generation.exists()
            return SimpleNamespace(returncode=next(removal_results))
        if command[1] == "bootstrap":
            assert not abandoned_generation.exists()
            assert (live_generation / "token").read_text() == "live-secret"
            return SimpleNamespace(returncode=next(bootstrap_results))
        return SimpleNamespace(returncode=0, stdout=str(temporary_root))

    monkeypatch.setattr(subprocess, "run", run)

    restart_agenix_launch_agent.restart_agenix_launch_agent(tmp_path)

    assert [command[1] for command in calls] == [
        "bootout",
        "print",
        "print",
        "print",
        "DARWIN_USER_TEMP_DIR",
        "bootstrap",
        "bootstrap",
    ]
    configuration = plistlib.loads(launch_agent.read_bytes())
    assert configuration["KeepAlive"] is False
    assert configuration["RunAtLoad"] is True
    assert configuration["ProgramArguments"] == ["/bin/sh", "mount-secrets"]
    assert stat.S_IMODE(launch_agent.stat().st_mode) == 0o444
    assert clock.seconds == 1.5


def test_removal_timeout_prevents_cleanup_and_bootstrap(monkeypatch, clock):
    calls = []

    def run(command, **options):
        calls.append(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", run)

    with pytest.raises(TimeoutError, match="Launch agent did not stop"):
        restart_agenix_launch_agent.stop_launch_agent("gui/502")

    assert clock.seconds == 10.0
    assert all(command[1] in {"bootout", "print"} for command in calls)


def test_bootstrap_failure_is_bounded_and_preserves_native_error(
    monkeypatch, launch_agent, clock
):
    def run(command, **options):
        return subprocess.CompletedProcess(command, 5, "", "Bootstrap failed: 5")

    monkeypatch.setattr(subprocess, "run", run)

    with pytest.raises(subprocess.CalledProcessError) as failure:
        restart_agenix_launch_agent.bootstrap_launch_agent("gui/502", launch_agent)

    assert clock.seconds == 10.0
    assert failure.value.returncode == 5
    assert failure.value.stderr == "Bootstrap failed: 5"


def test_successful_bootstrap_is_not_repeated(monkeypatch, launch_agent, clock):
    calls = []

    def run(command, **options):
        calls.append(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", run)

    restart_agenix_launch_agent.bootstrap_launch_agent("gui/502", launch_agent)

    assert len(calls) == 1
    assert clock.seconds == 0.0


def test_absent_launch_agent_does_not_touch_runtime(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *args, **options: calls.append(args))

    restart_agenix_launch_agent.restart_agenix_launch_agent(tmp_path)

    assert calls == []
