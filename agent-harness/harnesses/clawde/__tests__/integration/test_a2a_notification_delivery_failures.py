from concurrent.futures import ThreadPoolExecutor

from a2a_test_client import request_json


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
    content = owned_fleet.target.submitted[0]
    assert len(content.encode()) <= 32768
    delivered_count = content.count("From peer:\n")
    delivered = notifications[:delivered_count]
    assert 0 < delivered_count < len(notifications)
    assert content == "\n\n".join(
        f"From peer:\n{message['content']}" for message in delivered
    )
    unread = request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
        "messages"
    ]
    assert delivered + unread[:-1] == notifications
    assert unread[-1]["claimedSender"] == "late-peer"
    monkeypatch.setattr(session.backend, "send_input_text", send_input)
    for _ in notifications:
        if not unread:
            break
        owned_fleet.target.status = "idle"
        observe_fleet()
        unread = request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
            "messages"
        ]
    assert unread == []


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
    owned_fleet, observe_fleet
):
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
