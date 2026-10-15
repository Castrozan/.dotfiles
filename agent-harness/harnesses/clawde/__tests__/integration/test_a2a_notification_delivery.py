import json

from a2a_test_client import request_json


def test_observation_delivers_queued_notifications_when_idle(
    owned_fleet, observe_fleet
):
    _, notification = request_json(
        owned_fleet,
        "POST",
        "/agents/owned-peer/messages",
        {"claimedSender": "peer", "content": "result\nEnter C-c"},
    )
    observe_fleet()
    assert len(owned_fleet.target.submitted) == 1
    envelope = json.loads(owned_fleet.target.submitted[0].split("\n", 1)[1])
    batch = json.loads(envelope["content"])
    assert batch["messages"] == [notification]
    assert envelope["ownerPermission"] is False
    assert (
        request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1]["messages"]
        == []
    )
    observe_fleet()
    assert len(owned_fleet.target.submitted) == 1
    assert (
        owned_fleet.registry.session_named("owned-peer").task_store._tasks_by_id == {}
    )


def test_busy_and_occupied_agents_keep_notifications_until_idle(
    owned_fleet, observe_fleet
):
    for harness in ("claude", "codex", "opencode"):
        owned_fleet.target.harness = harness
        _, notification = request_json(
            owned_fleet,
            "POST",
            "/agents/owned-peer/messages",
            {"claimedSender": "peer", "content": "result"},
        )
        previous_count = len(owned_fleet.target.submitted)
        for status in ("working", "blocked", "unknown"):
            owned_fleet.target.status = status
            observe_fleet()
            assert len(owned_fleet.target.submitted) == previous_count
        owned_fleet.target.status = "idle"
        owned_fleet.target.draft = "unfinished question"
        observe_fleet()
        assert owned_fleet.target.draft == "unfinished question"
        assert len(owned_fleet.target.submitted) == previous_count
        assert request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
            "messages"
        ] == [notification]
        owned_fleet.target.draft = ""
        owned_fleet.target.status = "done"
        observe_fleet()
        assert len(owned_fleet.target.submitted) == previous_count + 1
        assert (
            request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
                "messages"
            ]
            == []
        )


def test_notification_delivery_waits_for_explicit_work_to_complete(
    owned_fleet, observe_fleet
):
    _, task = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "work"}
    )
    request_json(
        owned_fleet,
        "POST",
        "/agents/owned-peer/messages",
        {"claimedSender": "peer", "content": "result"},
    )
    observe_fleet()
    assert len(owned_fleet.target.submitted) == 1
    owned_fleet.target.status = "idle"
    observe_fleet()
    session = owned_fleet.registry.session_named("owned-peer")
    assert session.task_store.get_task(task["id"]).state == "completed"
    assert len(owned_fleet.target.submitted) == 2
    assert len(session.task_store._tasks_by_id) == 1


def test_empty_mailbox_does_not_probe_the_terminal(owned_fleet, observe_fleet):
    observe_fleet()
    assert owned_fleet.target.commands == []
