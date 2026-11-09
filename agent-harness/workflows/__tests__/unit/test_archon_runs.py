import json
import subprocess

import pytest

import archon_runs
from archon_runs import report_run, run_archon_json, wait_for_run


def completed_with(stdout, stderr=""):
    return subprocess.CompletedProcess(["archon"], 0, stdout=stdout, stderr=stderr)


def test_a_json_reply_is_returned(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_, **__: completed_with('{"ok": true, "runId": "r1"}'),
    )
    assert run_archon_json(["archon"])["runId"] == "r1"


def test_a_refused_request_surfaces_archon_error(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_, **__: completed_with(
            '{"ok": false, "error": "No default provider"}'
        ),
    )
    with pytest.raises(SystemExit, match="No default provider"):
        run_archon_json(["archon"])


def test_non_json_output_surfaces_stderr(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_, **__: completed_with("", "Error: Not in a git repository."),
    )
    with pytest.raises(SystemExit, match="Not in a git repository"):
        run_archon_json(["archon"])


def test_a_silent_archon_is_bounded(monkeypatch):
    def hang(*_, **keywords):
        raise subprocess.TimeoutExpired("archon", keywords["timeout"])

    monkeypatch.setattr(subprocess, "run", hang)
    with pytest.raises(SystemExit, match="no answer within 120 seconds"):
        run_archon_json(["archon"])


def test_a_wait_that_outlives_its_bound_still_reports(monkeypatch):
    def hang(*_, **keywords):
        raise subprocess.TimeoutExpired("archon", keywords["timeout"])

    monkeypatch.setattr(subprocess, "run", hang)
    assert wait_for_run("r1") is None


def test_a_report_waits_then_reads_the_run(monkeypatch):
    issued = []

    def answer(arguments, **_):
        issued.append(arguments[2])
        record = {
            "status": "completed",
            "terminal_record": {"returns": {"value": "done"}},
        }
        return completed_with(json.dumps(record))

    monkeypatch.setattr(subprocess, "run", answer)
    assert report_run("r1") == "status=completed\ndone"
    assert issued == ["wait", "get"]
    assert archon_runs.MAXIMUM_WAIT_SECONDS < 600
