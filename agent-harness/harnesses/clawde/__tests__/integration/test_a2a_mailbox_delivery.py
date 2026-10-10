from concurrent.futures import ThreadPoolExecutor

from a2a_test_client import request_json


def test_busy_callbacks_preserve_the_draft_and_do_not_replace_or_cancel_work(
    owned_fleet,
):
    status, task = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "work"}
    )
    assert status == 201
    owned_fleet.target.draft = "bunch"
    owned_fleet.target.commands.clear()
    notification_status, notification = request_json(
        owned_fleet,
        "POST",
        "/agents/owned-peer/messages",
        {"claimedSender": "Semiramis", "content": "clearance callback\nEnter C-c"},
    )
    assert notification_status == 202
    assert notification["trust"] == "untrusted_peer_data"
    assert notification["ownerPermission"] is False
    assert request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
        "messages"
    ] == [notification]
    assert request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
        "messages"
    ] == [notification]
    for _ in range(2):
        assert (
            request_json(
                owned_fleet,
                "POST",
                f"/agents/owned-peer/messages/{notification['id']}/ack",
            )[0]
            == 200
        )
    assert owned_fleet.target.draft == "bunch"
    assert owned_fleet.target.commands == []
    session = owned_fleet.registry.session_named("owned-peer")
    assert session.task_store.get_task(task["id"]).state == "working"
    assert len(session.task_store._tasks_by_id) == 1


def test_concurrent_http_senders_obey_capacity_without_discarding_unread_messages(
    owned_fleet,
):
    with ThreadPoolExecutor(max_workers=16) as senders:
        responses = list(
            senders.map(
                lambda index: request_json(
                    owned_fleet,
                    "POST",
                    "/agents/owned-peer/messages",
                    {"claimedSender": str(index), "content": f"result-{index}"},
                ),
                range(80),
            )
        )
    accepted = [document for status, document in responses if status == 202]
    assert len(accepted) == 64
    assert sum(status == 429 for status, _ in responses) == 16
    assert len({document["id"] for document in accepted}) == 64
    inbox = request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1]
    assert {message["id"] for message in inbox["messages"]} == {
        message["id"] for message in accepted
    }
    assert owned_fleet.target.commands == []
    acknowledged = accepted[0]["id"]
    request_json(owned_fleet, "POST", f"/agents/owned-peer/messages/{acknowledged}/ack")
    assert (
        request_json(
            owned_fleet,
            "POST",
            "/agents/owned-peer/messages",
            {"claimedSender": "peer", "content": "replacement"},
        )[0]
        == 202
    )


def test_notifications_follow_pane_identity_across_name_and_harness_changes(
    owned_fleet, transport_package
):
    _, notification = request_json(
        owned_fleet,
        "POST",
        "/agents/owned-peer/messages",
        {"claimedSender": "peer", "content": "before rename"},
    )
    renamed = transport_package.pane(
        "owned-pane", "owned-tab", "claude", "idle", "/different"
    )
    owned_fleet.registry.reconcile_against_the_live_fleet(
        [renamed], {"owned-tab": "renamed-peer"}
    )
    assert request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[0] == 404
    assert request_json(owned_fleet, "GET", "/agents/renamed-peer/messages")[1][
        "messages"
    ] == [notification]
    assert (
        request_json(
            owned_fleet,
            "POST",
            f"/agents/renamed-peer/messages/{notification['id']}/ack",
        )[0]
        == 200
    )
    assert (
        request_json(owned_fleet, "GET", "/agents/renamed-peer/messages")[1]["messages"]
        == []
    )
    replacement = transport_package.pane(
        "different-pane", "owned-tab", "codex", "idle", "/owned"
    )
    owned_fleet.registry.reconcile_against_the_live_fleet(
        [replacement], {"owned-tab": "renamed-peer"}
    )
    assert (
        request_json(owned_fleet, "GET", "/agents/renamed-peer/messages")[1][
            "recipientPaneId"
        ]
        == "different-pane"
    )
    assert (
        request_json(owned_fleet, "GET", "/agents/renamed-peer/messages")[1]["messages"]
        == []
    )
