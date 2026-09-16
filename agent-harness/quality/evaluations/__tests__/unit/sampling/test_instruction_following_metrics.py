import pytest

from integration.comparisons.ab_test_metrics import measure_instruction_following
from integration.comparisons.ab_test_models import SessionTrace, ToolCallEvent
from e2e.coaching.coached_scoring import (
    calculate_nps_from_tool_sequence_and_workspace,
    parse_tool_sequence,
)


def trace(*events):
    return SessionTrace(
        tool_calls=[ToolCallEvent(name, arguments) for name, arguments in events]
    )


def test_instruction_following_scores_observable_actions():
    compliant = trace(
        ("Glob", {}),
        ("Read", {}),
        ("Edit", {"new_string": "def calculate_total(): return 1"}),
        ("Bash", {"command": "git add total.py"}),
    )
    metrics = measure_instruction_following(compliant)
    assert metrics.score == 100 and metrics.read_to_edit_ratio == 1
    assert metrics.read_before_edit and metrics.used_specific_git_staging
    assert metrics.total_tool_calls == 4
    violated = trace(
        ("Write", {"content": "def calc():\n    # explanation\n    return 1"}),
        ("Read", {}),
        ("Bash", {"command": "find .; git add -A"}),
    )
    metrics = measure_instruction_following(violated)
    assert metrics.score == 15
    assert not any(
        [
            metrics.read_before_edit,
            metrics.used_glob_not_find,
            metrics.no_comments_in_written_code,
            metrics.used_descriptive_names,
            metrics.used_specific_git_staging,
        ]
    )
    no_read = measure_instruction_following(trace(("Write", {"content": "value = 1"})))
    assert not no_read.read_before_edit and no_read.read_to_edit_ratio == 0
    mixed = measure_instruction_following(
        trace(("Read", {}), ("Edit", {}), ("Write", {}), ("Grep", {}))
    )
    assert mixed.read_to_edit_ratio == 0.5 and mixed.score == 93
    assert measure_instruction_following(SessionTrace()).score == 50


def test_terminal_parser_recognizes_expanded_and_collapsed_calls():
    output = "\n".join(
        [
            "ignored prose",
            "● Read(main.py)",
            "⬤ Update(main.py)",
            "● Bash(long command",
            "  Read 3 files",
            "● Searched for 2 patterns",
            "● Custom(value)",
        ]
    )
    assert parse_tool_sequence(output) == [
        "Read",
        "Edit",
        "Bash",
        "Read",
        "Grep",
        "Custom",
    ]


@pytest.mark.parametrize(
    "tools,expected",
    [
        ([], 50),
        (["Read"], 40),
        (["Edit"], 30),
        (["Edit", "Read"], 40),
        (["Read", "Edit"], 65),
        (["Read", "Read", "Write"], 70),
    ],
)
def test_coached_score_accounts_for_read_order_and_ratio(
    monkeypatch, tmp_path, tools, expected
):
    from e2e.coaching import coached_scoring

    monkeypatch.setattr(
        coached_scoring.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("git unavailable")),
    )
    assert (
        calculate_nps_from_tool_sequence_and_workspace(tools, tmp_path, {}) == expected
    )
