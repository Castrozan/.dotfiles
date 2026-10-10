import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
import shorts_recovery
import shorts_runner
from shorts_store import TopicStore, write_document


@pytest.fixture
def held_run(tmp_path):
    config = {"timezone": "America/Sao_Paulo", "hours": [9, 15, 21]}
    run = tmp_path / "runs" / "2026-10-10-0900"
    run.mkdir(parents=True)
    episode = {
        "topic_key": "recovery-topic",
        "title": "Recovery topic",
        "summary": "An existing independently reserved subject and mechanism.",
    }
    write_document(run / "config.json", config)
    write_document(run / "status.json", {"status": "held"})
    write_document(run / "hold.json", {"reason": "voice failure"})
    write_document(run / "episode.json", episode)
    TopicStore(tmp_path).reserve(episode, run.name)
    return tmp_path, run, config


def test_queue_is_explicit_idempotent_and_keeps_topic_reservation(held_run):
    root, run, config = held_run
    shorts_recovery.queue_recoveries(root, [run.name], config)
    queue = shorts_recovery.queue_recoveries(root, [run.name], config)
    assert len(queue["runs"]) == 1
    assert queue["runs"][0]["status"] == "queued"
    assert json.loads((run / "status.json").read_text())["status"] == "held"
    assert (
        len([row for row in TopicStore(root).history() if row["run_id"] == run.name])
        == 1
    )


def test_existing_publication_dispatch_forbids_recovery(held_run):
    root, run, config = held_run
    write_document(run / "publication.json", {"status": "dispatch_recorded"})
    with pytest.raises(ValueError, match="no publication dispatch"):
        shorts_recovery.queue_recoveries(root, [run.name], config)
    assert not (root / shorts_recovery.QUEUE_FILE).exists()


@pytest.mark.parametrize(
    "hour,minute,expected",
    [
        (18, 30, True),
        (19, 0, False),
        (20, 59, False),
        (21, 0, False),
        (21, 1, False),
        (21, 3, True),
    ],
)
def test_future_slot_and_its_timer_accuracy_have_priority(hour, minute, expected):
    config = {"timezone": "America/Sao_Paulo", "hours": [9, 15, 21]}
    now = datetime(2026, 10, 10, hour, minute, tzinfo=ZoneInfo(config["timezone"]))
    assert shorts_recovery.window_available(config, now) is expected


def test_prior_evidence_is_archived_before_recovery(held_run):
    root, run, config = held_run
    (run / "agent-events.jsonl").write_text("original evidence\n")
    shorts_recovery.archive_attempt(run)
    archive = run / "recovery-attempts" / "001"
    assert json.loads((archive / "hold.json").read_text())["reason"] == "voice failure"
    assert (archive / "agent-events.jsonl").read_text() == "original evidence\n"
    assert not (run / "hold.json").exists()
    assert json.loads((run / "status.json").read_text())["status"] == "started"


@pytest.mark.parametrize("outcome", ["published", "held"])
def test_each_recovery_runs_once_and_records_its_actual_outcome(
    held_run, monkeypatch, outcome
):
    root, run, config = held_run
    shorts_recovery.queue_recoveries(root, [run.name], config)
    monkeypatch.setattr(shorts_recovery, "window_available", lambda config: True)
    monkeypatch.setattr(shorts_runner, "publisher_readiness", lambda *args: None)
    monkeypatch.setenv("SHORTS_RECOVERY_GOAL", "/recovery-goal.txt")
    calls = []

    def execute(directory, configuration):
        calls.append(directory)
        assert not (directory / "hold.json").exists()
        write_document(directory / "status.json", {"status": outcome})
        return {"status": outcome}

    monkeypatch.setattr(shorts_runner, "execute_run", execute)
    assert shorts_recovery.recover_next(root, config)["status"] == outcome
    assert shorts_recovery.recover_next(root, config)["status"] == "empty"
    assert calls == [run]
    assert shorts_recovery.read_queue(root)["runs"][0]["status"] == outcome


def test_recovery_cannot_overlap_an_active_production_run(held_run):
    import fcntl

    root, run, config = held_run
    shorts_recovery.queue_recoveries(root, [run.name], config)
    with (root / "production.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        assert shorts_recovery.recover_next(root, config)["status"] == "deferred"
    assert shorts_recovery.read_queue(root)["runs"][0]["status"] == "queued"
