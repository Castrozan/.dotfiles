import subprocess

from a2a_test_client import request_json


def test_native_submission_wait_failure_cannot_count_as_delivery(
    owned_fleet, transport_package, monkeypatch
):
    drive = transport_package.resolution.run_herdr_command

    def fail_native_wait(arguments):
        if arguments[:2] == ["agent", "prompt"]:
            assert arguments[4:] == [
                "--wait",
                "--until",
                "working",
                "--until",
                "blocked",
                "--timeout",
                "2000",
            ]
            return subprocess.CompletedProcess(arguments, 1, "", "agent_prompt_stalled")
        return drive(arguments)

    monkeypatch.setattr(
        transport_package.resolution, "run_herdr_command", fail_native_wait
    )
    status, task = request_json(
        owned_fleet,
        "POST",
        "/agents/owned-peer/tasks/send",
        {"input": "lost or delayed"},
    )
    assert status == 502
    assert task["state"] == "failed"
    assert "agent_prompt_stalled" in task["errorMessage"]
    assert owned_fleet.target.draft == ""


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
