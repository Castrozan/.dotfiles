import pytest

from a2a_test_client import request_json


@pytest.mark.parametrize(
    "inside",
    ["❯ unfinished", "❯ \ncontinued", "[Image #1]\n❯ ", "❯ \n[Image #1]"],
)
def test_claude_borders_do_not_hide_drafts_or_attachments(transport_package, inside):
    capture = "─" * 80 + "\n" + inside + "\n" + "─" * 80
    assert not transport_package.prompt_adapter.composer_is_observably_empty(
        capture, "claude"
    )


def test_claude_ansi_borders_enclose_an_empty_composer(transport_package):
    border = "\x1b[38;2;136;136;136m" + "─" * 80 + "\x1b[0m"
    capture = border + "\n❯\u00a0\n" + border + "\nfooter"
    assert transport_package.prompt_adapter.composer_is_observably_empty(
        capture, "claude"
    )


def test_claude_dim_prompt_suggestion_is_an_empty_composer(transport_package):
    border = "\x1b[0m\x1b[38;2;136;136;136m" + "─" * 80 + "\x1b[0m"
    suggestion = "\x1b[0m\x1b[2mrebuild once the toplevel finishes\x1b[0m"
    capture = border + "\n❯\u00a0" + suggestion + "\n" + border + "\nfooter"
    assert transport_package.prompt_adapter.composer_is_observably_empty(
        capture, "claude"
    )


@pytest.mark.parametrize(
    "prompt",
    [
        "❯ \x1b[2mcon\x1b[0mtinue",
        "❯ typed\x1b[2m suggestion\x1b[0m",
        "❯ \x1b[2mcontinue\x1b[22m now",
        "❯ \x1b[38;2;153;153;153mcontinue\x1b[0m",
    ],
)
def test_claude_text_that_is_not_wholly_dim_is_a_draft(transport_package, prompt):
    capture = "─" * 80 + "\n" + prompt + "\n" + "─" * 80
    assert not transport_package.prompt_adapter.composer_is_observably_empty(
        capture, "claude"
    )


def test_claude_prompt_suggestion_does_not_block_peer_work(owned_fleet):
    target = owned_fleet.target
    target.harness = "claude"
    target.suggestion = "rebuild once the toplevel finishes"
    response_status, task = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "peer work"}
    )
    assert response_status == 201
    assert task["state"] == "working"
    assert target.submitted == ["peer work"]


def test_claude_human_draft_still_blocks_peer_work(owned_fleet):
    target = owned_fleet.target
    target.harness = "claude"
    target.suggestion = "rebuild once the toplevel finishes"
    target.draft = "half typed"
    response_status, task = request_json(
        owned_fleet, "POST", "/agents/owned-peer/tasks/send", {"input": "peer work"}
    )
    assert response_status == 502
    assert "composer_occupied" in task["errorMessage"]
    assert target.draft == "half typed"
    assert not target.submitted
