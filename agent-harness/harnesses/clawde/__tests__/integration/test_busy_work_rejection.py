import subprocess

import pytest

from a2a_test_client import request_json


@pytest.mark.parametrize("harness", ["codex", "claude", "opencode"])
def test_busy_work_is_rejected_without_terminal_input(owned_fleet, harness):
    target = owned_fleet.target
    target.harness = harness
    target.status = "working"
    target.draft = "bunch\ncontinued human draft"
    status, rejected = request_json(
        owned_fleet,
        "POST",
        "/agents/owned-peer/tasks/send",
        {"input": "x" * 1025 + "\nclearance callback"},
    )
    assert status == 409
    assert rejected["state"] == "failed"
    assert "target_busy" in rejected["errorMessage"]
    assert target.draft == "bunch\ncontinued human draft"
    assert target.paste_buffer == ""
    assert not target.queued and not target.submitted
    assert all(
        command[:2] in (["pane", "get"], ["pane", "read"])
        for command in target.commands
    )
    assert not any("visible" in command for command in target.commands)


def test_previous_turn_completion_cannot_complete_rejected_work(
    owned_fleet, transport_package, monkeypatch
):
    target = owned_fleet.target
    target.status = "working"
    status, rejected = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "never queued"}
    )
    assert status == 409
    target.status = "idle"
    drive = transport_package.resolution.run_herdr_command

    def previous_turn_output(arguments):
        if arguments[:2] == ["pane", "read"] and "visible" not in arguments:
            return subprocess.CompletedProcess(
                arguments, 0, "• PREVIOUS_TURN_COMPLETED", ""
            )
        return drive(arguments)

    monkeypatch.setattr(
        transport_package.resolution, "run_herdr_command", previous_turn_output
    )
    session = owned_fleet.registry.session_named("owned-peer")
    session.coordinator.observe_once_and_apply_to_active_task()
    _, final = request_json(
        owned_fleet, "GET", f"/agents/owned-peer/tasks/{rejected['id']}"
    )
    assert final["state"] == "failed"
    assert final["output"] == ""
    assert not target.queued and not target.submitted
    next_status, accepted = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "idle work"}
    )
    assert next_status == 201 and accepted["id"] != rejected["id"]
    session.coordinator.observe_once_and_apply_to_active_task()
    _, next_observation = request_json(
        owned_fleet, "GET", f"/agents/owned-peer/tasks/{accepted['id']}"
    )
    assert next_observation["output"] == ""


def test_target_becoming_busy_during_preflight_is_rejected_before_paste(
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
    status, rejected = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "racing work"}
    )
    assert status == 409 and rejected["state"] == "failed"
    assert not target.paste_buffer and not target.draft
    assert not target.queued and not target.submitted
