import json

import pytest

from end_of_turn_format_guard_test_support import invoke_guard

from human_facing_reply_test_support import (
    labeled_reply_of,
    template_violations_in_reply,
)


@pytest.mark.parametrize("label", ["What is this session about?", "Done", "Next"])
@pytest.mark.parametrize("markup", ["{}:", "**{}:**", "__{}:__", "**{}**:", "**{}:"])
@pytest.mark.parametrize("separator", ["\n", "\r\n", "\r", "\n\n", "  \n", "\\\n"])
def test_label_content_cannot_start_on_the_next_line(label, markup, separator):
    reply = markup.format(label) + separator + "The check passed."

    violations = template_violations_in_reply(reply)

    assert any("same line" in violation for violation in violations)


@pytest.mark.parametrize("separator", ["\n", "\n\n", "<br>", "<BR />"])
def test_long_reply_requires_inline_label_content(separator):
    reply = labeled_reply_of(90).replace("**done:** ", "**done:**" + separator)

    assert any(
        "same line" in violation for violation in template_violations_in_reply(reply)
    )


@pytest.mark.parametrize(
    "suffix",
    ["", " ", "  ", "\\\n", "\n| # | Result |\n| --- | --- |\n| 1 | Passed |"],
)
def test_empty_label_lines_require_inline_content(suffix):
    assert template_violations_in_reply("**Done:**" + suffix)


@pytest.mark.parametrize(
    "content",
    [
        "The check passed.",
        "**The check passed.**",
        "`verified`",
        "https://example.org/result",
        "![proof](https://example.org/result.png)",
        "![](https://example.org/result.png)",
        "The check\npassed.",
        "The check passed.<br>More detail.",
    ],
)
def test_inline_content_and_later_continuations_are_allowed(content):
    assert template_violations_in_reply("**Done:** " + content) == []


@pytest.mark.parametrize(
    "example",
    [
        "```text\nDone:\nThe check passed.\n```",
        "> **Done:**\n> The check passed.",
        "| # | Format |\n| --- | --- |\n| 1 | Done: |\n| 2 | The check passed. |",
        "The example is `Done:` followed by a newline.",
    ],
)
def test_quoted_and_visual_examples_are_not_response_labels(example):
    assert template_violations_in_reply(example) == []


MARKDOWN_TABLE = "| # | Result |\n| --- | --- |\n| 1 | Passed |"
UNICODE_TABLE = (
    "┌───┬────────┐\n│ # │ Result │\n├───┼────────┤\n│ 1 │ Passed │\n└───┴────────┘"
)
ASCII_TABLE = (
    "+---+--------+\n| # | Result |\n+---+--------+\n| 1 | Passed |\n+---+--------+"
)
LABELS = ("What is this session about?", "Done", "Next")
TABLES = (
    MARKDOWN_TABLE,
    "# | Result\n--- | ---\n1 | Passed",
    UNICODE_TABLE,
    ASCII_TABLE,
    "╔═══╦════════╗\n║ # ║ Result ║\n╠═══╬════════╣\n║ 1 ║ Passed ║\n╚═══╩════════╝",
    "+--------+\n| Result |\n+--------+\n| Passed |\n+--------+",
    f"```markdown\n{MARKDOWN_TABLE}\n```",
    f"~~~text\n{ASCII_TABLE}\n~~~",
    "\n".join("    " + line for line in MARKDOWN_TABLE.splitlines()),
    "\n".join("> " + line for line in MARKDOWN_TABLE.splitlines()),
)


@pytest.mark.parametrize("label", LABELS)
@pytest.mark.parametrize("table", TABLES)
@pytest.mark.parametrize("inline_content", ("", " Verified."))
def test_tables_cannot_follow_reply_labels(label, table, inline_content):
    reply = f"**{label}:**{inline_content}\n\n{table}"

    violations = template_violations_in_reply(reply)

    assert any("table inside" in violation for violation in violations)


@pytest.mark.parametrize("table", TABLES)
def test_tables_can_precede_reply_labels(table):
    reply = f"{table}\n\n**Done:** Verified.\n\n**Next:** Nothing pending."

    assert template_violations_in_reply(reply) == []


@pytest.mark.parametrize(
    "content",
    (
        "The check passed.",
        "The check\npassed.",
        "Use `left | right`.",
        "Use a | b in the expression.",
        "See https://example.org/result.",
        "Verified.\n\n```text\n┌────────┐\n│ Client │\n└────────┘\n```",
        "Verified.\n\n```text\n+--------+\n| Client |\n+--------+\n```",
    ),
)
def test_label_prose_and_inline_code_remain_allowed(content):
    assert template_violations_in_reply(f"**Done:** {content}") == []


def test_table_feedback_identifies_the_owning_label():
    reply = (
        "**What is this session about?:** Reply formatting.\n\n"
        "**Done:** Verified.\n\n"
        f"{MARKDOWN_TABLE}\n\n**Next:** Nothing pending."
    )

    violations = template_violations_in_reply(reply)

    assert len(violations) == 1
    assert "done:" in violations[0]
    assert "above all labels" in violations[0]


@pytest.mark.parametrize("surface", ("claude", "codex", "opencode", "pi"))
def test_stop_hook_blocks_label_tables_and_accepts_moving_them_above(surface):
    payload = {
        "hook_event_name": "Stop",
        "session_id": "label-table-test",
        "reply_text": f"**Done:** Verified.\n\n{MARKDOWN_TABLE}",
    }

    blocked = invoke_guard(payload, surface=surface)

    feedback = json.loads(blocked.stdout)
    assert feedback["decision"] == "block"
    assert "table inside" in feedback["reason"]

    payload["reply_text"] = f"{MARKDOWN_TABLE}\n\n**Done:** Verified."
    allowed = invoke_guard(payload, surface=surface)

    assert allowed.returncode == 0
    assert allowed.stdout.strip() == ""
