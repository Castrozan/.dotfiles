from concurrent.futures import ThreadPoolExecutor

import pytest

from a2a_test_client import request_json

SEND_PATH = "/agents/owned-peer/tasks/send"


@pytest.mark.parametrize("harness", ["codex", "claude", "opencode"])
def test_work_reaches_a_busy_target_through_the_native_prompt(owned_fleet, harness):
    target = owned_fleet.target
    target.harness = harness
    target.status = "working"
    status, task = request_json(
        owned_fleet, "POST", SEND_PATH, {"input": "x" * 1025 + "\nclearance callback"}
    )
    assert status == 201
    assert task["state"] == "working"
    assert target.submitted == ["x" * 1025 + "\nclearance callback"]
    assert target.draft == target.paste_buffer == ""
    assert not any(
        command[:2] in (["pane", "send-text"], ["agent", "send-keys"])
        for command in target.commands
    )


@pytest.mark.parametrize("harness", ["codex", "claude", "opencode"])
def test_a_busy_target_holding_a_human_draft_receives_no_terminal_input(
    owned_fleet, harness
):
    target = owned_fleet.target
    target.harness = harness
    target.status = "working"
    target.draft = "bunch\ncontinued human draft"
    status, refused = request_json(
        owned_fleet, "POST", SEND_PATH, {"input": "clearance callback"}
    )
    assert status == 502
    assert refused["state"] == "failed"
    assert "composer_occupied" in refused["errorMessage"]
    assert target.draft == "bunch\ncontinued human draft"
    assert not target.submitted
    assert all(
        command[:2] in (["pane", "get"], ["pane", "read"])
        for command in target.commands
    )


def test_target_becoming_busy_during_preflight_still_receives_the_work(
    owned_fleet, transport_package, monkeypatch
):
    target = owned_fleet.target
    target.status = "idle"
    drive = transport_package.resolution.run_herdr_command

    def become_busy_after_capture(arguments):
        result = drive(arguments)
        if arguments[:2] == ["pane", "read"] and "visible" in arguments:
            target.status = "working"
        return result

    monkeypatch.setattr(
        transport_package.resolution, "run_herdr_command", become_busy_after_capture
    )
    status, task = request_json(
        owned_fleet, "POST", SEND_PATH, {"input": "racing work"}
    )
    assert status == 201 and task["state"] == "working"
    assert target.submitted == ["racing work"]


def test_every_dispatch_to_one_target_is_its_own_task_until_the_turn_ends(owned_fleet):
    inputs = ["first", "second", "third"]
    tasks = [
        request_json(owned_fleet, "POST", SEND_PATH, {"input": text}) for text in inputs
    ]
    assert [status for status, _ in tasks] == [201, 201, 201]
    task_ids = [task["id"] for _, task in tasks]
    assert len(set(task_ids)) == 3
    assert owned_fleet.target.submitted == inputs
    session = owned_fleet.registry.session_named("owned-peer")
    session.coordinator.observe_once_and_apply_to_active_task()
    for task_id, text in zip(task_ids, inputs):
        _, task = request_json(
            owned_fleet, "GET", f"/agents/owned-peer/tasks/{task_id}"
        )
        assert (task["state"], task["input"]) == ("working", text)
    owned_fleet.target.status = "idle"
    session.coordinator.observe_once_and_apply_to_active_task()
    assert [session.task_store.get_task(task_id).state for task_id in task_ids] == [
        "completed"
    ] * 3
    assert not session.is_holding_an_unfinished_task()


def test_concurrent_senders_all_reach_the_target_exactly_once(owned_fleet):
    inputs = [f"work-{index}" for index in range(12)]
    with ThreadPoolExecutor(max_workers=len(inputs)) as senders:
        responses = list(
            senders.map(
                lambda text: request_json(
                    owned_fleet, "POST", SEND_PATH, {"input": text}
                ),
                inputs,
            )
        )
    assert [status for status, _ in responses] == [201] * len(inputs)
    assert sorted(owned_fleet.target.submitted) == sorted(inputs)
    assert len({task["id"] for _, task in responses}) == len(inputs)


def test_cancel_interrupts_the_turn_and_every_task_riding_it(owned_fleet):
    task_ids = [
        request_json(owned_fleet, "POST", SEND_PATH, {"input": text})[1]["id"]
        for text in ("first", "second")
    ]
    owned_fleet.target.commands.clear()
    status, canceled = request_json(
        owned_fleet, "POST", f"/agents/owned-peer/tasks/{task_ids[1]}/cancel"
    )
    assert (status, canceled["state"]) == (200, "canceled")
    assert owned_fleet.target.commands == [["pane", "send-keys", "owned-pane", "C-c"]]
    session = owned_fleet.registry.session_named("owned-peer")
    assert [session.task_store.get_task(task_id).state for task_id in task_ids] == [
        "canceled",
        "canceled",
    ]
    repeated_status, repeated = request_json(
        owned_fleet, "POST", f"/agents/owned-peer/tasks/{task_ids[0]}/cancel"
    )
    assert (repeated_status, repeated["state"]) == (200, "canceled")
    assert len(owned_fleet.target.commands) == 1
    owned_fleet.target.status = "idle"
    session.coordinator.observe_once_and_apply_to_active_task()
    assert session.task_store.get_task(task_ids[0]).state == "canceled"
    assert request_json(owned_fleet, "POST", SEND_PATH, {"input": "next"})[0] == 201
