import subprocess

import pytest

from a2a_test_client import request_json


def test_stale_empty_composer_cannot_count_as_a_submission_receipt(
    owned_fleet, transport_package, monkeypatch
):
    drive = transport_package.resolution.run_herdr_command

    def stale_screen(arguments):
        if arguments[:2] == ["pane", "read"] and "visible" in arguments:
            return subprocess.CompletedProcess(
                arguments, 0, "\n› \x1b[2mAsk Codex to do anything\x1b[0m\n\nfooter", ""
            )
        return drive(arguments)

    monkeypatch.setattr(transport_package.resolution, "run_herdr_command", stale_screen)
    monkeypatch.setattr(
        transport_package.prompt_adapter, "DELIVERY_OBSERVATION_TIMEOUT_SECONDS", 0.01
    )
    status, task = request_json(
        owned_fleet,
        "POST",
        "/agents/owned-peer/tasks/send",
        {"input": "lost or delayed"},
    )
    assert status == 502
    assert task["state"] == "failed"
    assert "submission_unconfirmed" in task["errorMessage"]


@pytest.mark.parametrize("initial_status", ["idle", "working"])
def test_tab_selects_submission_at_key_handling_time_when_busy_state_changes(
    owned_fleet, transport_package, monkeypatch, initial_status
):
    target = owned_fleet.target
    target.status = initial_status
    drive = transport_package.resolution.run_herdr_command

    def change_state_during_paste(arguments):
        if arguments[:2] == ["pane", "send-text"]:
            target.status = "working" if initial_status == "idle" else "idle"
        return drive(arguments)

    monkeypatch.setattr(
        transport_package.resolution, "run_herdr_command", change_state_during_paste
    )
    status, _ = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "racing work"}
    )
    assert status == 201
    assert len(target.queued if target.status == "working" else target.submitted) == 1
    assert not any("Enter" in command[3:] for command in target.commands)
