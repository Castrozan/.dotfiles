import json
import smtplib
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock
from zoneinfo import ZoneInfo

import pytest
from shorts_notifications import mail, state


@pytest.fixture
def publication(tmp_path, monkeypatch):
    run = tmp_path / "runs" / "2026-10-10-0900"
    run.mkdir(parents=True)
    data = {
        "status": "published",
        "video_id": "hHHQZJKvxis",
        "url": "https://www.youtube.com/shorts/hHHQZJKvxis",
        "published_at": "2026-10-10T21:25:35+00:00",
    }
    for name, value in {
        "publication": data,
        "status": data,
        "config": {"channel_id": state.CHANNEL},
        "episode": {"title": "The snake"},
    }.items():
        (run / f"{name}.json").write_text(json.dumps(value))
    (run / "recovery-attempts").mkdir()
    ledger = tmp_path / "ledger"
    ledger.mkdir()
    monkeypatch.setattr(state, "recent_runs", lambda root: [run])
    return tmp_path, run, ledger


def test_completed_publication_is_enqueued_once_and_keeps_recovered_slot(publication):
    root, run, ledger = publication
    state.collect(root, ledger)
    state.collect(root, ledger)
    records = list(state.pending(ledger))
    assert len(records) == 1
    event = records[0][1]["event"]
    assert event["recovered"] and event["run_id"] == run.name
    message = mail.message_for(event)
    assert message["To"] == "castro.lucas290@gmail.com"
    assert message["Message-ID"] == "<shorts-hHHQZJKvxis@chise.local>"
    assert event["url"] in message.get_content()
    assert "09:00 (São Paulo)" in message.get_content()


@pytest.mark.parametrize(
    "file,field,value",
    [
        ("status", "status", "started"),
        ("publication", "status", "dispatch_recorded"),
        ("config", "channel_id", "another-channel"),
        ("publication", "video_id", "../../invalid"),
        ("publication", "url", "https://example.org/"),
        ("publication", "published_at", "2026-10-09T21:00:00+00:00"),
    ],
)
def test_incomplete_or_untrusted_publication_is_not_emailed(
    publication, file, field, value
):
    root, run, ledger = publication
    path = run / f"{file}.json"
    document = json.loads(path.read_text())
    document[field] = value
    path.write_text(json.dumps(document))
    if file == "publication":
        (run / "status.json").write_text(json.dumps(document))
    state.collect(root, ledger)
    assert list(state.pending(ledger)) == []


def test_transport_acceptance_is_durable_and_does_not_modify_publication(publication):
    root, run, ledger = publication
    before = (run / "publication.json").read_bytes()
    state.collect(root, ledger)
    path, record = next(state.pending(ledger))
    server = Mock()
    mail.attempt(path, record, Path("unused"), lambda secret: server)
    assert state.read_json(path)["status"] == "sent"
    state.collect(root, ledger)
    assert list(state.pending(ledger)) == []
    server.send_message.assert_called_once()
    assert (run / "publication.json").read_bytes() == before


@pytest.mark.parametrize(
    "failure,expected",
    [
        (smtplib.SMTPDataError(451, b"Temporary rejection"), "pending"),
        (smtplib.SMTPRecipientsRefused({"recipient": (450, b"Retry")}), "pending"),
        (smtplib.SMTPServerDisconnected("Acknowledgement lost"), "delivery_uncertain"),
    ],
)
def test_retries_only_follow_known_nonacceptance(publication, failure, expected):
    root, run, ledger = publication
    state.collect(root, ledger)
    path, record = next(state.pending(ledger))
    server = Mock()
    server.send_message.side_effect = failure
    mail.attempt(path, record, Path("unused"), lambda secret: server)
    assert state.read_json(path)["status"] == expected
    assert bool(list(state.pending(ledger))) is (expected == "pending")
    assert state.read_json(run / "publication.json")["status"] == "published"


def test_auth_failure_can_retry_without_publication_retry(publication):
    root, run, ledger = publication
    state.collect(root, ledger)
    path, record = next(state.pending(ledger))
    connect = Mock(side_effect=smtplib.SMTPAuthenticationError(535, b"Rejected"))
    mail.attempt(path, record, Path("unused"), connect)
    assert state.read_json(path)["status"] == "pending"
    server = Mock()
    mail.attempt(path, record, Path("unused"), lambda secret: server)
    assert state.read_json(path)["attempts"] == 2
    assert state.read_json(path)["status"] == "sent"


def test_crash_during_data_is_never_automatically_retried(publication):
    root, run, ledger = publication
    state.collect(root, ledger)
    path, record = next(state.pending(ledger))
    server = Mock()
    server.send_message.side_effect = SystemExit
    with pytest.raises(SystemExit):
        mail.attempt(path, record, Path("unused"), lambda secret: server)
    assert state.read_json(path)["status"] == "delivery_uncertain"
    assert list(state.pending(ledger)) == []


def test_discovery_is_bounded_to_twenty_one_scheduled_slots(tmp_path):
    now = datetime(2026, 10, 10, 18, tzinfo=ZoneInfo("America/Sao_Paulo"))
    runs = list(state.recent_runs(tmp_path, now))
    assert len(runs) == 21
    assert runs[0].name == "2026-10-10-0900"
    assert runs[-1].name == "2026-10-04-2100"


def test_symlinked_and_oversized_inputs_are_rejected(publication):
    root, run, ledger = publication
    path = run / "episode.json"
    path.unlink()
    path.symlink_to(run / "status.json")
    state.collect(root, ledger)
    assert list(state.pending(ledger)) == []
    path.unlink()
    path.write_text(" " * 65537)
    state.collect(root, ledger)
    assert list(state.pending(ledger)) == []


@pytest.mark.parametrize("outcome", ["sent", "delivery_uncertain"])
def test_existing_gmail_receipt_prevents_smtp_duplicate(publication, outcome):
    root, run, ledger = publication
    receipt = {
        "status": outcome,
        "video_id": "hHHQZJKvxis",
        "recipient": state.RECIPIENT,
        "transport": "connected-gmail",
    }
    (run / "email-notification.json").write_text(json.dumps(receipt))
    state.collect(root, ledger)
    assert list(state.pending(ledger)) == []
    assert state.read_json(ledger / "hHHQZJKvxis.json")["status"] == outcome
