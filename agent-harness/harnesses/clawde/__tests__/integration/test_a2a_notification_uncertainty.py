"""Accepted-but-unconfirmed delivery must never be automatically replayed."""

import pytest
from a2a_test_client import request_json


def publish(fleet, content="result"):
    return request_json(
        fleet,
        "POST",
        "/agents/owned-peer/messages",
        {"claimedSender": "peer", "content": content},
    )[1]


def lose_acknowledgment(fleet, monkeypatch):
    session = fleet.registry.session_named("owned-peer")
    original = session.backend.send_input_text

    def accepted_then_error(content):
        original(content)
        raise RuntimeError("synthetic acknowledgment failure after acceptance")

    monkeypatch.setattr(session.backend, "send_input_text", accepted_then_error)
    return session, original


@pytest.mark.parametrize("harness", ["codex", "claude", "opencode"])
def test_accepted_then_error_cannot_replay_when_idle(
    owned_fleet, observe_fleet, monkeypatch, harness
):
    owned_fleet.target.harness = harness
    message = publish(owned_fleet)
    lose_acknowledgment(owned_fleet, monkeypatch)
    for _ in range(3):
        owned_fleet.target.status = "idle"
        observe_fleet()
    assert owned_fleet.target.submitted == ["From peer:\nresult"]
    unread = request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
        "messages"
    ]
    assert unread == [{**message, "deliveryState": "uncertain"}]


def test_delivery_restart_and_rename_keep_uncertainty(
    owned_fleet, observe_fleet, transport_package, monkeypatch
):
    message = publish(owned_fleet)
    session, original = lose_acknowledgment(owned_fleet, monkeypatch)
    observe_fleet()
    monkeypatch.setattr(session.backend, "send_input_text", original)
    owned_fleet.target.status = "idle"
    restarted = type(session.notification_delivery)(
        session.notification_mailbox, session.coordinator
    )
    restarted.flush_once()
    owned_fleet.registry.reconcile_against_the_live_fleet(
        [owned_fleet.pane], {"owned-tab": "renamed-peer"}
    )
    renamed = owned_fleet.registry.session_named("renamed-peer")
    renamed.notification_delivery.flush_once()
    assert owned_fleet.target.submitted == ["From peer:\nresult"]
    unread = request_json(owned_fleet, "GET", "/agents/renamed-peer/messages")[1][
        "messages"
    ]
    assert unread == [{**message, "deliveryState": "uncertain"}]


def test_explicit_ack_recovers_only_selected_message_without_sending(
    owned_fleet, observe_fleet, monkeypatch
):
    message = publish(owned_fleet)
    session, original = lose_acknowledgment(owned_fleet, monkeypatch)
    observe_fleet()
    monkeypatch.setattr(session.backend, "send_input_text", original)
    distinct = publish(owned_fleet)
    before = list(owned_fleet.target.commands)
    for _ in range(2):
        assert (
            request_json(
                owned_fleet, "POST", f"/agents/owned-peer/messages/{message['id']}/ack"
            )[0]
            == 200
        )
    assert owned_fleet.target.commands == before
    assert request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
        "messages"
    ] == [distinct]
    owned_fleet.target.status = "idle"
    observe_fleet()
    assert owned_fleet.target.submitted == ["From peer:\nresult"] * 2
    observe_fleet()
    assert len(owned_fleet.target.submitted) == 2


def test_distinct_notification_can_deliver_while_uncertain_one_is_quarantined(
    owned_fleet, observe_fleet, monkeypatch
):
    uncertain = publish(owned_fleet)
    session, original = lose_acknowledgment(owned_fleet, monkeypatch)
    observe_fleet()
    monkeypatch.setattr(session.backend, "send_input_text", original)
    publish(owned_fleet, "different result")
    owned_fleet.target.status = "idle"
    observe_fleet()
    assert owned_fleet.target.submitted == [
        "From peer:\nresult",
        "From peer:\ndifferent result",
    ]
    unread = request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
        "messages"
    ]
    assert unread == [{**uncertain, "deliveryState": "uncertain"}]


def test_fresh_daemon_state_does_not_reconstruct_or_replay_notifications(
    owned_fleet, observe_fleet, transport_package, monkeypatch
):
    publish(owned_fleet)
    lose_acknowledgment(owned_fleet, monkeypatch)
    observe_fleet()
    owned_fleet.target.status = "idle"
    restarted = transport_package.registry(transport_package.metadata({}), "")
    restarted.reconcile_against_the_live_fleet(
        [owned_fleet.pane], {"owned-tab": "owned-peer"}
    )
    session = restarted.session_named("owned-peer")
    assert session.notification_mailbox.read() == []
    session.notification_delivery.flush_once()
    assert owned_fleet.target.submitted == ["From peer:\nresult"]


def test_native_prompt_error_after_acceptance_is_not_preflight_deferral(
    owned_fleet, observe_fleet, transport_package, monkeypatch
):
    import subprocess

    message = publish(owned_fleet)
    drive = transport_package.resolution.run_herdr_command

    def accepted_then_timeout(arguments):
        result = drive(arguments)
        if arguments[:2] == ["agent", "prompt"]:
            return subprocess.CompletedProcess(arguments, 1, "", "timeout")
        return result

    monkeypatch.setattr(
        transport_package.resolution, "run_herdr_command", accepted_then_timeout
    )
    for _ in range(3):
        owned_fleet.target.status = "idle"
        observe_fleet()
    assert owned_fleet.target.submitted == ["From peer:\nresult"]
    unread = request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
        "messages"
    ]
    assert unread == [{**message, "deliveryState": "uncertain"}]


def test_interrupted_delivery_cannot_replay_after_worker_restart(
    owned_fleet, observe_fleet, monkeypatch
):
    message = publish(owned_fleet)
    session = owned_fleet.registry.session_named("owned-peer")
    original = session.backend.send_input_text

    def interrupted_after_acceptance(content):
        original(content)
        raise KeyboardInterrupt("synthetic worker interruption")

    monkeypatch.setattr(
        session.backend, "send_input_text", interrupted_after_acceptance
    )
    with pytest.raises(KeyboardInterrupt):
        observe_fleet()
    monkeypatch.setattr(session.backend, "send_input_text", original)
    owned_fleet.target.status = "idle"
    restarted = type(session.notification_delivery)(
        session.notification_mailbox, session.coordinator
    )
    restarted.flush_once()
    assert owned_fleet.target.submitted == ["From peer:\nresult"]
    assert session.notification_mailbox.read()[0].to_json_serializable_dict() == {
        **message,
        "deliveryState": "uncertain",
    }
