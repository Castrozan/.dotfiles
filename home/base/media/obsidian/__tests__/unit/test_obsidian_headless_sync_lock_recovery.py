import importlib.util
from pathlib import Path

import pytest

OBSIDIAN_MODULE_DIRECTORY = Path(__file__).resolve().parents[2]
SYNC_SCRIPT_PATH = OBSIDIAN_MODULE_DIRECTORY / "scripts" / "obsidian-headless-sync.py"


def load_sync_script():
    specification = importlib.util.spec_from_file_location(
        "obsidian_headless_sync", SYNC_SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


sync_script = load_sync_script()


class SyncHarness:
    def __init__(self, monkeypatch, tmp_path):
        self.monkeypatch = monkeypatch
        self.vault = tmp_path / "vault"
        (self.vault / ".obsidian").mkdir(parents=True)
        self.lock = self.vault / ".obsidian" / ".sync.lock"
        self.attempt_log = tmp_path / "attempts.log"
        self.attempt_log.touch()
        self.npm_prefix = tmp_path / "npm"
        (self.npm_prefix / "bin").mkdir(parents=True)
        monkeypatch.setattr(
            sync_script, "LOCK_REFRESH_OBSERVATION_WINDOW_SECONDS", 0.02
        )
        monkeypatch.setenv("NODE_BIN_DIR", str(tmp_path / "node"))
        monkeypatch.setenv("NPM_PREFIX", str(self.npm_prefix))
        monkeypatch.setenv("VAULT_PATH", str(self.vault))
        monkeypatch.setenv("TIMEOUT_BIN", str(self.install_timeout_shim()))

    def install_timeout_shim(self) -> Path:
        shim = self.npm_prefix / "bin" / "timeout"
        shim.write_text('#!/usr/bin/env bash\nshift 3\nexec "$@"\n')
        shim.chmod(0o755)
        return shim

    def install_ob(self, body: str) -> None:
        fake_ob = self.npm_prefix / "bin" / "ob"
        fake_ob.write_text(f"#!/usr/bin/env bash\necho x >> {self.attempt_log}\n{body}")
        fake_ob.chmod(0o755)

    def install_ob_losing_the_race(self, losses: int) -> None:
        self.install_ob(
            f"if [ $(wc -l < {self.attempt_log}) -le {losses} ]; then\n"
            f"  mkdir -p {self.lock}\n"
            f'  echo "{sync_script.LOCK_UNAVAILABLE_MESSAGE}" >&2\n'
            "  exit 1\n"
            "fi\n"
            'echo "Fully synced"\n'
        )

    @property
    def attempts(self) -> int:
        return len(self.attempt_log.read_text().splitlines())

    def run(self) -> int:
        return sync_script.main()


@pytest.fixture
def harness(monkeypatch, tmp_path):
    return SyncHarness(monkeypatch, tmp_path)


def test_the_script_the_nix_module_runs_exists():
    assert SYNC_SCRIPT_PATH.is_file()


def test_a_lost_lock_verification_race_is_retried_until_it_wins(harness, capsys):
    harness.install_ob_losing_the_race(losses=2)

    exit_code = harness.run()

    assert exit_code == 0, (
        "ob loses a coin flip inside acquire() whenever the lock mtime it just wrote "
        "does not round trip through a float, so a single attempt fails roughly half "
        "the time and only a retry keeps the vault syncing"
    )
    assert harness.attempts == 3
    assert "Fully synced" in capsys.readouterr().out


def test_the_orphaned_lock_a_lost_race_leaves_behind_is_discarded(harness):
    harness.install_ob_losing_the_race(losses=1)

    harness.run()

    assert not harness.lock.exists(), (
        "acquire() throws after creating the lock and release() only runs in a finally "
        "that starts later, so the orphan it strands would poison every later pass"
    )


def test_a_permanently_lost_race_gives_up_loudly_rather_than_looping(harness, capsys):
    harness.install_ob_losing_the_race(losses=999)

    exit_code = harness.run()

    assert exit_code == 1
    assert harness.attempts == sync_script.SYNC_ATTEMPT_LIMIT
    assert "Gave up" in capsys.readouterr().err


def test_a_failure_that_is_not_the_lock_race_is_never_retried(harness, capsys):
    harness.install_ob('echo "Sync failed: network unreachable" >&2\nexit 3\n')

    exit_code = harness.run()

    assert exit_code == 3, (
        "retrying an auth or network failure eight times per pass would hammer the "
        "server and bury the real error"
    )
    assert harness.attempts == 1
    assert "network unreachable" in capsys.readouterr().err


def test_a_lock_a_live_sync_keeps_refreshing_is_left_alone(harness, monkeypatch):
    harness.install_ob_losing_the_race(losses=0)
    harness.lock.mkdir()
    refreshing_times = iter([1_000_000_000, 2_000_000_000])
    monkeypatch.setattr(
        sync_script, "lock_modification_time", lambda _: next(refreshing_times)
    )

    exit_code = harness.run()

    assert exit_code == 0
    assert harness.attempts == 0, (
        "ob refreshes its lock every second while genuinely syncing, so a changing "
        "mtime means a real sync holds it and stealing it would run two syncs at once"
    )
    assert harness.lock.exists()


def test_a_stale_lock_no_one_refreshes_is_removed_and_the_sync_proceeds(harness):
    harness.install_ob_losing_the_race(losses=0)
    harness.lock.mkdir()

    exit_code = harness.run()

    assert exit_code == 0
    assert harness.attempts == 1, (
        "a lock whose mtime never moves belongs to a dead run, and the old sixty "
        "second window skipped whole passes waiting on it"
    )


def test_a_missing_ob_install_fails_without_touching_the_lock(harness):
    assert harness.run() == 1
