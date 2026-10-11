from pathlib import Path
from unittest.mock import Mock

import pytest
from shorts_notifications import mail, state


def test_retry_batch_prioritizes_untried_and_oldest_attempt(tmp_path):
    for identifier, attempted in (
        ("first", "2026-10-10T21:01:00"),
        ("second", "2026-10-10T21:02:00"),
        ("new", ""),
    ):
        state.save(
            tmp_path / f"{identifier}.json",
            {"status": "pending", "attempted_at": attempted},
        )
    assert [path.stem for path, _ in state.pending(tmp_path)] == [
        "new",
        "first",
        "second",
    ]


def test_existing_smtp_route_uses_verified_tls_and_closes_on_auth_failure(
    tmp_path, monkeypatch
):
    password = tmp_path / "test-credential"
    password.write_text("mock-secret")
    server = Mock()
    factory = Mock(return_value=server)
    monkeypatch.setattr(mail.smtplib, "SMTP", factory)
    assert mail.connect(password) is server
    factory.assert_called_once_with("smtp.gmail.com", 587, timeout=30)
    assert server.starttls.call_args.kwargs["context"].check_hostname
    server.login.assert_called_once_with(state.RECIPIENT, "mock-secret")
    server.login.side_effect = mail.smtplib.SMTPAuthenticationError(535, b"Refused")
    with pytest.raises(mail.smtplib.SMTPAuthenticationError):
        mail.connect(password)
    server.close.assert_called_once()


def test_missing_credential_never_dispatches(tmp_path):
    server = Mock()
    record = {
        "status": "pending",
        "attempts": 0,
        "event": {
            "video_id": "hHHQZJKvxis",
            "run_id": "2026-10-10-0900",
            "recovered": True,
            "title": "Published title",
            "url": "https://www.youtube.com/shorts/hHHQZJKvxis",
        },
    }
    connector = Mock(side_effect=PermissionError)
    mail.attempt(tmp_path / "state.json", record, Path("unreadable"), connector)
    assert record["status"] == "pending"
    assert record["error"] == "PermissionError"
    server.send_message.assert_not_called()
