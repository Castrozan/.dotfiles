import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from a2a_test_client import request_json


def test_work_dispatch_and_a_busy_target_keep_one_task(owned_fleet):
    status, first = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "Enter\nC-c"}
    )
    assert status == 201
    invocation = next(
        command
        for command in owned_fleet.target.commands
        if command[:2] == ["pane", "send-text"]
    )
    assert invocation[:3] == ["pane", "send-text", "owned-pane"]
    frame = json.loads(invocation[3].split("\n", 1)[1])
    assert frame["content"] == "Enter\nC-c"
    assert frame["trust"] == "untrusted_peer_data"
    assert frame["ownerPermission"] is False
    session = owned_fleet.registry.session_named("owned-peer")
    session.backend._last_activity_at_epoch_seconds = time.time() - 60
    session.task_store.get_task(first["id"]).created_at_epoch_seconds -= 60
    session.coordinator.observe_once_and_apply_to_active_task()
    second_status, second = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "second"}
    )
    assert second_status == 409
    assert second["id"] == first["id"]
    assert session.task_store.get_task(first["id"]).state == "working"
    owned_fleet.target.status = "idle"
    session.coordinator.observe_once_and_apply_to_active_task()
    assert session.task_store.get_task(first["id"]).state == "completed"


def test_failed_delivery_preserves_partial_input_and_releases_the_task(
    owned_fleet,
):
    owned_fleet.target.fail_submission = True
    status, failed = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "rejected"}
    )
    assert status == 502
    assert failed["state"] == "failed"
    assert "agent_blocked" in failed["errorMessage"]
    owned_fleet.target.fail_submission = False
    next_status, next_task = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "next"}
    )
    assert next_status == 502
    assert next_task["id"] != failed["id"]
    assert "composer_occupied" in next_task["errorMessage"]
    owned_fleet.target.paste_buffer = ""
    owned_fleet.target.draft = ""
    assert (
        request_json(
            owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "next"}
        )[0]
        == 201
    )


def test_pending_delivery_cannot_complete_during_an_observation(transport_package):
    entered_delivery = threading.Event()
    release_delivery = threading.Event()

    class OwnedDelayedBackend:
        def send_input_text(self, text):
            entered_delivery.set()
            assert release_delivery.wait(2)

        def observe(self):
            return transport_package.observation("", True, 0, agent_is_busy=False)

    coordinator = transport_package.coordinator.ActiveTaskCoordinator(
        transport_package.store(),
        OwnedDelayedBackend(),
        auto_complete_idle_timeout_seconds=0,
    )
    with ThreadPoolExecutor(max_workers=1) as workers:
        submission = workers.submit(coordinator.submit_new_task_if_idle, "work")
        assert entered_delivery.wait(2)
        try:
            coordinator.observe_once_and_apply_to_active_task()
            assert coordinator.is_holding_an_unfinished_task()
            assert coordinator.submit_new_task_if_idle("second")[1] is False
        finally:
            release_delivery.set()
        assert submission.result(timeout=2)[0].state == "working"
