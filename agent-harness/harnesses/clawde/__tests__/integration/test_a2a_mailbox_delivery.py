from concurrent.futures import ThreadPoolExecutor
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


def test_failed_delivery_keeps_notifications_for_retry(owned_fleet, observe_fleet):
    _, notification = request_json(
        owned_fleet,
        "POST",
        "/agents/owned-peer/messages",
        {"claimedSender": "peer", "content": "result"},
    )
    owned_fleet.target.fail_submission = True
    observe_fleet()
    assert request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
        "messages"
    ] == [notification]
    owned_fleet.target.fail_submission = False
    observe_fleet()
    assert len(owned_fleet.target.submitted) == 1


def test_batch_is_bounded_and_preserves_later_arrivals(
    owned_fleet, observe_fleet, monkeypatch
):
    notifications = []
    for index in range(8):
        _, notification = request_json(
            owned_fleet,
            "POST",
            "/agents/owned-peer/messages",
            {"claimedSender": "peer", "content": str(index) + "x" * 7900},
        )
        notifications.append(notification)
    session = owned_fleet.registry.session_named("owned-peer")
    send_input = session.backend.send_input_text

    def send_and_publish(content):
        send_input(content)
        request_json(
            owned_fleet,
            "POST",
            "/agents/owned-peer/messages",
            {"claimedSender": "late-peer", "content": "arrived during delivery"},
        )

    monkeypatch.setattr(session.backend, "send_input_text", send_and_publish)
    observe_fleet()
    envelope = json.loads(owned_fleet.target.submitted[0].split("\n", 1)[1])
    assert len(envelope["content"].encode()) <= 32768
    delivered = json.loads(envelope["content"])["messages"]
    assert 0 < len(delivered) < len(notifications)
    unread = request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
        "messages"
    ]
    assert delivered + unread[:-1] == notifications
    assert unread[-1]["claimedSender"] == "late-peer"
    monkeypatch.setattr(session.backend, "send_input_text", send_input)
    while unread:
        owned_fleet.target.status = "idle"
        observe_fleet()
        unread = request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
            "messages"
        ]


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


def test_explicit_work_cannot_submit_during_notification_delivery(
    owned_fleet, observe_fleet, monkeypatch
):
    import threading

    entered_submission = threading.Event()
    release_submission = threading.Event()
    session = owned_fleet.registry.session_named("owned-peer")
    send_input = session.backend.send_input_text

    def delayed_submission(content):
        entered_submission.set()
        assert release_submission.wait(timeout=2)
        send_input(content)

    monkeypatch.setattr(session.backend, "send_input_text", delayed_submission)
    request_json(
        owned_fleet,
        "POST",
        "/agents/owned-peer/messages",
        {"claimedSender": "peer", "content": "result"},
    )
    with ThreadPoolExecutor(max_workers=2) as callers:
        delivery = callers.submit(observe_fleet)
        assert entered_submission.wait(timeout=2)
        task_submission = callers.submit(
            request_json,
            owned_fleet,
            "POST",
            "/agents/owned-peer/tasks/send",
            {"input": "new task"},
        )
        release_submission.set()
        delivery.result(timeout=3)
        assert task_submission.result(timeout=3)[0] == 409
    assert len(owned_fleet.target.submitted) == 1


def test_unconfirmed_submission_keeps_the_message_and_occupied_composer(
    owned_fleet, observe_fleet, transport_package, monkeypatch
):
    monkeypatch.setattr(
        transport_package.prompt_adapter, "DELIVERY_OBSERVATION_TIMEOUT_SECONDS", 0.01
    )
    _, notification = request_json(
        owned_fleet,
        "POST",
        "/agents/owned-peer/messages",
        {"claimedSender": "peer", "content": "result"},
    )
    owned_fleet.target.ignore_submission = True
    observe_fleet()
    draft = owned_fleet.target.draft
    assert draft
    assert request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
        "messages"
    ] == [notification]
    observe_fleet()
    assert owned_fleet.target.draft == draft
    assert owned_fleet.target.submitted == []
