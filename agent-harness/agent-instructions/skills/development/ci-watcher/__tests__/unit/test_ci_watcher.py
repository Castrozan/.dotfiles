import json
import subprocess
from unittest.mock import Mock

import pytest

from ci_watcher import watcher as ci_watcher
from forge.repository import Repository


@pytest.fixture
def github_run(monkeypatch, tmp_path):
    result = {
        "databaseId": 42,
        "attempt": 2,
        "headSha": "a" * 40,
        "status": "completed",
        "conclusion": "success",
        "url": "https://github.com/owner/repository/actions/runs/42",
        "jobs": [{"name": "first"}, {"name": "second"}],
    }
    process = Mock()
    process.wait.return_value = 0
    calls = []

    def start(command, **options):
        calls.append(command)
        options["stdout"].write("native watcher progress\n")
        return process

    def finish(command, **options):
        calls.append(command)
        if "--json" in command:
            return subprocess.CompletedProcess(command, 0, json.dumps(result))
        options["stdout"].write("first job evidence\nsecond job evidence\n")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(ci_watcher.tempfile, "mkdtemp", lambda **options: str(tmp_path))
    monkeypatch.setattr(
        ci_watcher,
        "resolve_repository",
        lambda **options: Repository("github", "github.com", "owner/repository"),
    )
    monkeypatch.setattr(ci_watcher.subprocess, "Popen", start)
    monkeypatch.setattr(ci_watcher.subprocess, "run", finish)
    return result, process, calls


@pytest.mark.parametrize(
    "conclusion,status",
    [("success", 0), ("failure", 1), ("cancelled", 1), ("skipped", 1), ("neutral", 1)],
)
def test_collects_one_terminal_verdict_and_all_job_logs(
    github_run, tmp_path, capsys, conclusion, status
):
    result, process, calls = github_run
    result["conclusion"] = conclusion
    process.wait.return_value = status

    assert ci_watcher.watch(42, "owner/repository") == status

    retained = json.loads((tmp_path / "result.json").read_text())
    assert retained["conclusion"] == conclusion
    assert retained["jobs"] == result["jobs"]
    assert retained["attempt"] == 2
    assert (
        tmp_path / "run.log"
    ).read_text() == "first job evidence\nsecond job evidence\n"
    assert calls[0] == [
        "gh",
        "run",
        "watch",
        "42",
        "--repo",
        "https://github.com/owner/repository",
        "--compact",
        "--exit-status",
        "--interval",
        "30",
    ]
    assert calls[-1][-3:] == ["--attempt", "2", "--log"]
    assert len(capsys.readouterr().out.splitlines()) == 2
    process.wait.assert_called_once_with(timeout=3600)


def test_watcher_error_does_not_claim_an_active_run_failed(github_run, tmp_path):
    result, process, calls = github_run
    result["status"] = "in_progress"
    result["conclusion"] = ""
    process.wait.return_value = 1

    assert ci_watcher.watch(42) == 2

    assert json.loads((tmp_path / "result.json").read_text())["outcome"] == "error"
    assert len(calls) == 2


@pytest.mark.parametrize(
    "interruption,status,outcome",
    [
        (KeyboardInterrupt(), 130, "interrupted"),
        (subprocess.TimeoutExpired("gh", 10), 124, "timeout"),
    ],
)
def test_interruption_stops_only_the_local_watcher(
    github_run, tmp_path, interruption, status, outcome
):
    _, process, calls = github_run
    process.wait.side_effect = [interruption, 0]

    assert ci_watcher.watch(42, timeout=10) == status

    process.terminate.assert_called_once_with()
    process.kill.assert_not_called()
    assert len(calls) == 1
    assert json.loads((tmp_path / "result.json").read_text())["outcome"] == outcome


def test_timeout_reaps_a_watcher_that_ignores_termination(github_run):
    _, process, _ = github_run
    process.wait.side_effect = [
        subprocess.TimeoutExpired("gh", 10),
        subprocess.TimeoutExpired("gh", 5),
        0,
    ]

    assert ci_watcher.watch(42, timeout=10) == 124

    process.kill.assert_called_once_with()


def test_missing_log_evidence_is_a_watcher_error(github_run, monkeypatch, tmp_path):
    result, _, _ = github_run

    def unavailable(command, **options):
        if "--json" in command:
            return subprocess.CompletedProcess(command, 0, json.dumps(result))
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(ci_watcher.subprocess, "run", unavailable)

    assert ci_watcher.watch(42) == 2

    assert json.loads((tmp_path / "result.json").read_text())["outcome"] == "error"
