import json

import pytest

from end_of_turn_format_guard_test_support import (
    WELL_FORMED_REPLY,
    invoke_guard,
    stop_payload,
    write_transcript_with_final_assistant_reply,
)
from human_facing_reply_test_support import template_violations_in_reply


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
            tmp_path, f"{WELL_FORMED_REPLY}\n{visual}"
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
        "reply_text": "| Result |\n| --- |\n| Passed |",
    }
    blocked = invoke_guard(payload, surface=surface)
    feedback = json.loads(blocked.stdout)
    assert feedback["decision"] == "block"
    assert "index" in feedback["reason"]

    payload["reply_text"] = "| # | Result |\n| --- | --- |\n| 1 | Passed |"
    allowed = invoke_guard(payload, surface=surface)
    assert allowed.returncode == 0
    assert allowed.stdout.strip() == ""
