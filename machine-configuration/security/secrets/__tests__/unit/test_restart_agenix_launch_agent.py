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
