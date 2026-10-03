import json
import subprocess

import pytest

from ci_watcher import gitlab, watcher
from forge.repository import Repository
from forge import native

REPOSITORY = Repository("gitlab", "gitlab.example", "group/project")


@pytest.fixture
def pipeline(monkeypatch, tmp_path):
    result = {
        "id": 42,
        "sha": "a" * 40,
        "status": "success",
        "web_url": "https://gitlab.example/group/project/-/pipelines/42",
    }
    jobs = [
        {
            "id": 1,
            "name": "first",
            "status": "success",
            "started_at": "now",
            "web_url": "job/1",
        },
        {
            "id": 2,
            "name": "second",
            "status": "success",
            "started_at": "now",
            "web_url": "job/2",
        },
    ]
    calls = []
    monkeypatch.setattr(watcher.tempfile, "mkdtemp", lambda **options: str(tmp_path))
    monkeypatch.setattr(watcher, "resolve_repository", lambda **options: REPOSITORY)
    monkeypatch.setattr(gitlab, "gitlab_json", lambda *args, **options: result)
    monkeypatch.setattr(gitlab, "gitlab_pages", lambda *args, **options: jobs)

    def trace(command, **options):
        calls.append(command)
        options["stdout"].write(f"evidence for {command[2]}\n")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(gitlab.subprocess, "run", trace)
    return result, jobs, calls


@pytest.mark.parametrize(
    "conclusion,status",
    [("success", 0), ("failed", 1), ("canceled", 1), ("skipped", 1)],
)
def test_terminal_verdict_retains_every_job(
    pipeline, tmp_path, capsys, conclusion, status
):
    result, jobs, calls = pipeline
    result["status"] = conclusion
    assert watcher.watch(42) == status
    retained = json.loads((tmp_path / "result.json").read_text())
    assert retained["conclusion"] == conclusion
    assert retained["jobs"] == jobs
    assert retained["repository"] == REPOSITORY.url
    assert len(calls) == 2
    assert all(command[-2:] == ["--hostname", REPOSITORY.hostname] for command in calls)
    assert "jobs/1/trace" in (tmp_path / "run.log").read_text()
    assert "jobs/2/trace" in (tmp_path / "run.log").read_text()
    assert len(capsys.readouterr().out.splitlines()) == 2


def test_pending_run_retains_failed_job_early_and_waits_for_final_verdict(
    pipeline, monkeypatch, tmp_path
):
    result, jobs, calls = pipeline
    states = iter(["running", "failed"])
    jobs[0]["status"] = "failed"
    monkeypatch.setattr(
        gitlab,
        "gitlab_json",
        lambda *args, **options: {**result, "status": next(states)},
    )

    def wait(interval):
        assert interval <= 30
        assert len(calls) == 1
        assert (tmp_path / "job-1.log").exists()

    monkeypatch.setattr(gitlab.time, "sleep", wait)
    assert watcher.watch(42) == 1
    assert len(calls) == 2
    assert (tmp_path / "watch.log").read_text() == "running\nfailed\n"


def test_skipped_unstarted_job_has_no_trace_request(pipeline, tmp_path):
    result, jobs, calls = pipeline
    result["status"] = "skipped"
    for job in jobs:
        job.update(status="skipped", started_at=None)
    assert watcher.watch(42) == 1
    assert calls == []
    assert "no trace available" in (tmp_path / "run.log").read_text()


@pytest.mark.parametrize(
    "error,status,outcome",
    [
        (KeyboardInterrupt(), 130, "interrupted"),
        (subprocess.TimeoutExpired("glab", 1), 124, "timeout"),
        (subprocess.CalledProcessError(1, ["glab", "api"]), 2, "error"),
        (ValueError("invalid metadata"), 2, "error"),
    ],
)
def test_local_error_does_not_cancel_remote_pipeline(
    pipeline, monkeypatch, tmp_path, error, status, outcome
):
    _, _, calls = pipeline

    def fail(*args, **options):
        raise error

    monkeypatch.setattr(gitlab, "gitlab_json", fail)
    assert watcher.watch(42) == status
    assert json.loads((tmp_path / "result.json").read_text())["outcome"] == outcome
    assert calls == []


def test_missing_trace_is_a_watcher_error(pipeline, monkeypatch, tmp_path):
    def unavailable(command, **options):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(gitlab.subprocess, "run", unavailable)
    assert watcher.watch(42) == 2
    assert json.loads((tmp_path / "result.json").read_text())["outcome"] == "error"


def test_pipeline_lookup_cannot_extend_the_timeout_before_job_pagination(
    pipeline, monkeypatch
):
    result, _, calls = pipeline
    clock = [0]
    monkeypatch.setattr(gitlab.time, "monotonic", lambda: clock[0])

    def delayed(*args, **options):
        clock[0] = 2
        return result

    monkeypatch.setattr(gitlab, "gitlab_json", delayed)
    monkeypatch.setattr(gitlab, "gitlab_pages", native.gitlab_pages)
    assert watcher.watch(42, timeout=1) == 124
    assert calls == []
