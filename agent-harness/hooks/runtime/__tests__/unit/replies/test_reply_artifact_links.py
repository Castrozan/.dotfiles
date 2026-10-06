import json

import pytest

from end_of_turn_format_guard_test_support import invoke_guard
from human_facing_reply_test_support import template_violations_in_reply


@pytest.mark.parametrize(
    "destination",
    [
        "https://",
        "https://example.com/unrelated",
        "https://github.com/example/repo/pull/18",
        "https://gitlab.example.com/group/repo/-/merge_requests/17",
        "https:///example/repo/pull/17",
    ],
)
def test_artifact_references_need_a_matching_destination(destination):
    assert template_violations_in_reply("PR #17 is ready. " + destination)


@pytest.mark.parametrize(
    "reply",
    [
        "PR #17 is ready: https://github.com/example/repo/pull/17.",
        "PR #17 is ready.\n\n| # | Review |\n| --- | --- |\n| 1 | https://github.com/example/repo/pull/17 |",
        "MR !17 is ready: https://gitlab.example.com/group/repo/-/merge_requests/17",
        "The pull request is ready: https://github.com/example/repo/pull/17",
    ],
)
def test_links_in_prose_and_tables_can_satisfy_artifact_references(reply):
    assert template_violations_in_reply(reply) == []


def test_an_artifact_named_in_a_table_needs_a_link():
    reply = "| # | Artifact | Status |\n| --- | --- | --- |\n| 1 | PR #17 | ready |"

    assert template_violations_in_reply(reply)


def test_each_numbered_artifact_needs_its_own_destination():
    reply = "PR #17 and PR #18 are ready: https://github.com/example/repo/pull/17"

    assert template_violations_in_reply(reply)


def test_a_quoted_url_does_not_link_an_artifact():
    assert template_violations_in_reply(
        'PR #17 is ready. The input included "https://".'
    )


@pytest.mark.parametrize("article", ["The", "This", "That"])
@pytest.mark.parametrize(
    "kind,route", [("pull request", "pull"), ("merge request", "merge_requests")]
)
def test_long_form_numbered_references_keep_their_identifier(article, kind, route):
    reply = f"{article} {kind} #17 is ready: https://example.com/group/repo/{route}/18"

    assert template_violations_in_reply(reply)
    assert template_violations_in_reply(reply.replace("/18", "/17")) == []


@pytest.mark.parametrize(
    "reply",
    [
        "Review: [result](https://example.com/result).",
        "[https://example.com/result](https://example.com/result)",
        "Review: [result][review]\n\n[review]: https://example.com/result",
        "Review: <https://example.com/result>",
        '<a href="https://example.com/result">result</a>',
        '<div>\n<a href="https://example.com/result">result</a>\n</div>',
        "| # | Result |\n| --- | --- |\n| 1 | [result](https://example.com/result) |",
        "[source](/tmp/source.py)",
        "Contact: <engineer@example.com>",
        "\x1b]8;;https://example.com/result\x1b\\result\x1b]8;;\x1b\\",
    ],
)
def test_formatted_links_are_rejected_in_reply_prose(reply):
    violations = template_violations_in_reply(reply)

    assert any("bare URLs" in violation for violation in violations)


@pytest.mark.parametrize(
    "reply",
    [
        "Review: https://example.com/result",
        "Review: https://example.com/result?branch=main&job=build#logs",
        "| # | Result |\n| --- | --- |\n| 1 | https://example.com/result |",
        "Literal syntax: `[result](https://example.com/result)`.",
        'Literal syntax: `<a href="https://example.com/result">result</a>`.',
        "```markdown\n[result](https://example.com/result)\n```",
        '```html\n<a href="https://example.com/result">result</a>\n```',
        "> [quoted source](https://example.com/result)",
        '> <a href="https://example.com/result">quoted source</a>',
        "![figure](https://example.com/figure.png)",
    ],
)
def test_raw_urls_and_literal_examples_remain_allowed(reply):
    assert template_violations_in_reply(reply) == []


@pytest.mark.parametrize("surface", ("claude", "codex", "opencode", "pi"))
def test_shared_stop_guard_rejects_hidden_urls_and_accepts_raw_urls(surface):
    payload = {
        "hook_event_name": "Stop",
        "session_id": "raw-url-contract",
        "reply_text": "Review: [result](https://example.com/result)",
    }

    rejected = json.loads(invoke_guard(payload, surface=surface).stdout)

    assert rejected["decision"] == "block"
    assert "bare URLs" in rejected["reason"]

    payload["reply_text"] = "Review: https://example.com/result"
    accepted = json.loads(invoke_guard(payload, surface=surface).stdout or "{}")

    assert accepted.get("decision") != "block"
