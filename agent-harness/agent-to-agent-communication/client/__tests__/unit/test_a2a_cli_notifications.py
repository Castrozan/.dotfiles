import argparse

import pytest
from a2a_cli import commands, peer_transport
from a2a_cli.__main__ import build_argument_parser


def test_stable_pane_identity_survives_a_name_change_and_takes_precedence_over_a_name():
    directory = {
        "renamed": {"paneId": "owned-pane", "endpoint": "http://owned/renamed"},
        "owned-pane": {"paneId": "other-pane", "endpoint": "http://owned/other"},
    }
    assert (
        peer_transport.resolve_peer_endpoint(directory, "owned-pane")
        == "http://owned/renamed"
    )


def test_notification_submission_uses_the_mailbox_and_preserves_sender_claim_and_literal_text(
    monkeypatch,
):
    requests = []

    def record(method, url, payload=None):
        requests.append((method, url, payload))
        return 202, {
            "id": "notification",
            "trust": "untrusted_peer_data",
            "ownerPermission": False,
        }

    monkeypatch.setattr(peer_transport, "request_peer_json", record)
    receipt = peer_transport.notify_peer("http://owned/peer", "Semiramis", "Enter\nC-c")
    assert requests == [
        (
            "POST",
            "http://owned/peer/messages",
            {"claimedSender": "Semiramis", "content": "Enter\nC-c"},
        )
    ]
    assert receipt["ownerPermission"] is False


@pytest.mark.parametrize("status", [400, 413, 429, 503])
def test_notification_rejections_are_reported_without_retrying(monkeypatch, status):
    requests = []

    def reject(*arguments):
        requests.append(arguments)
        return status, {"error": "rejected"}

    monkeypatch.setattr(peer_transport, "request_peer_json", reject)
    with pytest.raises(peer_transport.PeerRequestFailure, match=str(status)):
        peer_transport.notify_peer("http://owned/peer", "Semiramis", "result")
    assert len(requests) == 1


def test_inbox_reads_do_not_acknowledge_and_acknowledgement_is_a_separate_request(
    monkeypatch,
):
    requests = []

    def record(method, url, payload=None):
        requests.append((method, url, payload))
        return 200, {}

    monkeypatch.setattr(peer_transport, "request_peer_json", record)
    peer_transport.read_peer_inbox("http://owned/peer")
    peer_transport.acknowledge_peer_notification("http://owned/peer", "notification/id")
    assert requests == [
        ("GET", "http://owned/peer/messages", None),
        ("POST", "http://owned/peer/messages/notification%2Fid/ack", None),
    ]


def test_notify_requires_an_explicit_sender_claim():
    with pytest.raises(SystemExit):
        build_argument_parser().parse_args(["notify", "owned-pane", "result"])


def test_inbox_output_escapes_untrusted_terminal_control_sequences(monkeypatch, capsys):
    monkeypatch.setattr(
        commands, "read_peer_inbox", lambda _: {"content": "\x1b]0;forged\x07"}
    )
    commands.command_inbox(
        argparse.Namespace(agent="owned-pane"),
        {"peer": {"paneId": "owned-pane", "endpoint": "http://owned/peer"}},
    )
    output = capsys.readouterr().out
    assert "\x1b" not in output
    assert "\\u001b" in output
