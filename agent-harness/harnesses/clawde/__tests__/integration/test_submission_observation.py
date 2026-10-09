import subprocess

from a2a_test_client import request_json


def test_scrolled_submission_receipt_is_confirmed_from_recent_history(
    owned_fleet, transport_package, monkeypatch
):
    target = owned_fleet.target
    drive = transport_package.resolution.run_herdr_command

    def scroll_submission_out_of_view(arguments):
        result = drive(arguments)
        if arguments[:2] != ["pane", "read"] or not target.submitted:
            return result
        if "visible" in arguments:
            return subprocess.CompletedProcess(
                arguments, 0, "\n› \x1b[2mAsk Codex to do anything\x1b[0m\n\nfooter", ""
            )
        return subprocess.CompletedProcess(arguments, 0, target.submitted[-1], "")

    monkeypatch.setattr(
        transport_package.resolution,
        "run_herdr_command",
        scroll_submission_out_of_view,
    )
    monkeypatch.setattr(
        transport_package.prompt_adapter, "DELIVERY_OBSERVATION_TIMEOUT_SECONDS", 0.01
    )
    status, task = request_json(
        owned_fleet,
        "POST",
        "/agents/owned-peer/tasks/send",
        {"input": "x" * 2563},
    )
    assert status == 201, task
    assert len(target.submitted) == 1


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


def test_harness_change_during_preflight_fails_before_composer_mutation(
    owned_fleet, transport_package, monkeypatch
):
    target = owned_fleet.target
    drive = transport_package.resolution.run_herdr_command

    def change_harness_after_capture(arguments):
        result = drive(arguments)
        if arguments[:2] == ["pane", "read"] and "visible" in arguments:
            target.harness = "claude"
        return result

    monkeypatch.setattr(
        transport_package.resolution, "run_herdr_command", change_harness_after_capture
    )
    status, _ = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "racing work"}
    )
    assert status == 502
    assert not target.queued and not target.submitted
    assert not target.draft and not target.paste_buffer
