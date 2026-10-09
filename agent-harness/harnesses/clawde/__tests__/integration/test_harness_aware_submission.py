import json

import pytest

from a2a_test_client import request_json


@pytest.mark.parametrize("status", ["idle", "working"])
@pytest.mark.parametrize(
    "content", ["short", "a" * 1025 + "\nsecond\tline", "x" * 8192]
)
def test_codex_submission_flushes_paste_and_uses_the_harness_submission_key(
    owned_fleet, status, content
):
    owned_fleet.target.status = status
    response_status, task = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": content}
    )
    assert response_status == 201
    target = owned_fleet.target
    delivered = target.queued if status == "working" else target.submitted
    assert len(delivered) == 1
    assert json.loads(delivered[0].split("\n", 1)[1])["content"] == content
    assert target.draft == target.paste_buffer == ""
    assert not target.submitted if status == "working" else not target.queued
    assert [
        command for command in target.commands if command[:2] == ["agent", "send-keys"]
    ] == [
        [
            "agent",
            "send-keys",
            "owned-pane",
            "Right",
            "Tab",
        ]
    ]
    assert task["state"] == "working"


@pytest.mark.parametrize(
    "draft",
    [
        "bunch",
        "human\ncontinued",
        "Ask Codex to do anything",
        "[Pasted Content 1024 chars] trailing",
    ],
)
@pytest.mark.parametrize("status", ["idle", "working"])
def test_existing_human_draft_fails_before_any_terminal_input(
    owned_fleet, draft, status
):
    target = owned_fleet.target
    target.draft = draft
    target.status = status
    response_status, task = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "peer work"}
    )
    assert response_status == 502
    assert task["state"] == "failed"
    assert "composer_occupied" in task["errorMessage"]
    assert target.draft == draft
    assert all(
        command[:2] in (["pane", "get"], ["pane", "read"])
        for command in target.commands
    )


def test_successful_key_write_without_submission_is_a_terminal_failure(
    owned_fleet, transport_package, monkeypatch
):
    monkeypatch.setattr(
        transport_package.prompt_adapter, "DELIVERY_OBSERVATION_TIMEOUT_SECONDS", 0.01
    )
    owned_fleet.target.ignore_submission = True
    status, task = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "undelivered"}
    )
    assert status == 502
    assert task["state"] == "failed"
    assert "submission_unconfirmed" in task["errorMessage"]
    assert owned_fleet.target.draft
    assert not owned_fleet.target.queued


@pytest.mark.parametrize("status", ["blocked", "unknown"])
def test_unready_target_fails_before_paste(owned_fleet, status):
    owned_fleet.target.status = status
    response_status, task = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "work"}
    )
    assert response_status == 502
    assert task["state"] == "failed"
    assert not owned_fleet.target.paste_buffer
    assert all(
        command[:2] == ["pane", "get"] for command in owned_fleet.target.commands
    )


def test_other_supported_harness_retains_native_prompt_submission(owned_fleet):
    owned_fleet.target.harness = "claude"
    owned_fleet.target.status = "idle"
    status, _ = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "native work"}
    )
    assert status == 201
    assert len(owned_fleet.target.submitted) == 1
    assert not any(
        command[:2] == ["pane", "send-text"] for command in owned_fleet.target.commands
    )


@pytest.mark.parametrize(
    "capture",
    [
        "\n› \x1b[38;2;2;100;200mAsk Codex to do anything\x1b[0m\n\nfooter",
        "\n› \x1b[2mbunch\x1b[0m\n\nfooter",
        "\n› \x1b[2mAsk Codex to do anything\x1b[0m\n  continued draft\n\nfooter",
        "[Image #1]\n› \x1b[2mAsk Codex to do anything\x1b[0m\n\nfooter",
        "› \x1b[2mAsk Codex to do anything\x1b[0m",
    ],
)
def test_ambiguous_composer_and_color_values_cannot_pass_the_draft_guard(
    transport_package, capture
):
    assert not transport_package.prompt_adapter.composer_is_observably_empty(
        capture, "codex"
    )
