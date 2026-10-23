import json

import pytest

from end_of_turn_format_guard_test_support import (
    WELL_FORMED_REPLY,
    assistant_text_event,
    invoke_guard,
    stop_payload,
    user_event,
    write_transcript_from_events,
    write_transcript_with_final_assistant_reply,
)
from human_facing_reply_test_support import template_violations_in_reply

FIFTEEN_ROW_TABLE = "| # | Finding |\n| --- | --- |\n" + "\n".join(
    f"| {number} | finding-{number} |" for number in range(1, 16)
)


def test_allows_every_humanize_visual_representation(tmp_path):
    visual_representations = (
        "```diff\n- old behavior\n+ new behavior\n```",
        "| # | Option | Scope |\n|---|---|---|\n| 1 | Automatic | Every system |",
        "```text\nState A -> State B\nState B -failure-> State A\n```",
        "```text\nClient -> API: request\nAPI -> Client: result\n```",
        "```text\nOwner\n├── Reader policy\n└── Hook mechanics\n```",
        "```text\n[Input] -> [Decision] -> [Output]\n```",
        "```text\nif eligible(system):\n    create_administrator(system)\n```",
    )

    for visual in visual_representations:
        transcript = write_transcript_with_final_assistant_reply(
            tmp_path, f"{visual}\n\n{WELL_FORMED_REPLY}"
        )
        result = invoke_guard(stop_payload(transcript))
        assert result.stdout.strip() == ""


@pytest.mark.parametrize(
    "reply",
    [
        "| Result |\n| --- |\n| Passed |",
        "| Result | # |\n| --- | --- |\n| Passed | 1 |",
        "| # | Result |\n| --- | --- |\n| | Passed |",
        "| # | Result |\n| --- | --- |\n| 0 | Passed |",
        "| # | Result |\n| --- | --- |\n| 2 | Passed |",
        "| # | Result |\n| --- | --- |\n| 1 | Passed |\n| 1 | Passed |",
        "| # | Result |\n| --- | --- |\n| 1 | Passed |\n| 3 | Passed |",
        "| # | Result |\n| --- | --- |\n| one | Passed |",
        "| # | Result |\n| --- | --- |\n| 01 | Passed |",
        "> | Result |\n> | --- |\n> | Passed |",
        "- Results\n\n  | Result |\n  | --- |\n  | Passed |",
    ],
)
def test_every_rendered_table_requires_sequential_row_indexes(reply):
    if reply.startswith("|"):
        reply = f"Summary:\n\n{reply}"
    assert any(
        "table 1" in violation and "index" in violation
        for violation in template_violations_in_reply(reply)
    )


@pytest.mark.parametrize(
    "reply",
    [
        "| # | Result |\n| --- | --- |\n| 1 | Passed |\n| 2 | Failed |",
        "# | Result\n--- | ---\n1 | Passed\n2 | Failed",
        "| **#** | Result |\n| ---: | :--- |\n| **1** | Passed |\n| `2` | Failed |",
        "| # | Result |\n| --- | --- |",
        "| # | Result |\n| --- | --- |\n| 1 | Escaped \\| pipe |",
        "```markdown\n| Result |\n| --- |\n| Passed |\n```",
        "~~~markdown\n| Result |\n| --- |\n| Passed |\n~~~",
        "    | Result |\n    | --- |\n    | Passed |",
        "The expression is left | right.",
    ],
)
def test_indexed_tables_and_literal_examples_pass(reply):
    assert template_violations_in_reply(reply) == []


def test_each_table_restarts_its_index_and_is_checked_independently():
    table = "| # | Result |\n| --- | --- |\n| 1 | Passed |"
    assert template_violations_in_reply(table + "\n\n" + table) == []

    violations = template_violations_in_reply(
        table + "\n\n" + table.replace("| 1 |", "| 2 |")
    )
    assert len(violations) == 1
    assert "table 2" in violations[0]


@pytest.mark.parametrize("surface", ("claude", "codex", "opencode", "pi"))
def test_stop_hook_blocks_an_unindexed_table_and_accepts_its_repair(surface):
    payload = {
        "hook_event_name": "Stop",
        "session_id": "table-index-test",
        "reply_text": "Summary:\n\n| Result |\n| --- |\n| Passed |",
    }
    blocked = invoke_guard(payload, surface=surface)
    feedback = json.loads(blocked.stdout)
    assert feedback["decision"] == "block"
    assert "index" in feedback["reason"]

    payload["reply_text"] = "Summary:\n\n| # | Result |\n| --- | --- |\n| 1 | Passed |"
    allowed = invoke_guard(payload, surface=surface)
    assert allowed.returncode == 0
    assert allowed.stdout.strip() == ""


@pytest.mark.parametrize(
    "user_request,exempt",
    [
        ("show the 15 findings as a table", True),
        ("Tables, please", True),
        ("monte uma tabela com tudo", True),
        ("list every finding", False),
        ("check the timetable", False),
    ],
)
def test_a_table_request_lifts_the_row_ceiling(user_request, exempt):
    violations = template_violations_in_reply(
        FIFTEEN_ROW_TABLE, user_request=user_request
    )

    assert (violations == []) == exempt


def test_a_table_request_keeps_the_index_column_rule():
    reply = "Summary:\n\n| Finding |\n| --- |\n" + "\n".join(
        "| finding |" for _ in range(15)
    )

    violations = template_violations_in_reply(reply, user_request="as a table")

    assert any("index column" in item for item in violations)
    assert not any("data rows" in item for item in violations)


def test_stop_hook_accepts_a_long_table_the_user_asked_for(tmp_path):
    transcript = write_transcript_from_events(
        tmp_path,
        [
            user_event("give me every finding in one table"),
            assistant_text_event(FIFTEEN_ROW_TABLE),
        ],
    )

    result = invoke_guard(stop_payload(transcript))

    assert result.returncode == 0
    assert result.stdout.strip() == ""


@pytest.mark.parametrize(
    "hook_feedback",
    [
        "Stop hook feedback:\nReply breaks the enforced interactive rules "
        "(table 1 has 15 data rows, past its 5-row ceiling).",
        '<hook_prompt hook_run_id="stop:1">table 1 has 15 data rows</hook_prompt>',
    ],
)
def test_hook_feedback_naming_a_table_is_not_a_table_request(tmp_path, hook_feedback):
    transcript = write_transcript_from_events(
        tmp_path,
        [
            user_event("list every finding"),
            assistant_text_event(FIFTEEN_ROW_TABLE),
            user_event(hook_feedback),
            assistant_text_event(FIFTEEN_ROW_TABLE),
        ],
    )

    feedback = json.loads(invoke_guard(stop_payload(transcript)).stdout)

    assert feedback["decision"] == "block"
    assert "data rows" in feedback["reason"]
