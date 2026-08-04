"""Shell splitting is quote-aware, because a separator inside quotes is text.

The guards that route through this module forbid RUNNING something, so they
exempt a match that sits inside a read-only inspection segment. Finding that
segment means splitting the command the way a shell would: a semicolon or a
pipe inside quotes is an argument character, not a boundary. Splitting on it
blindly cut a grep in half and blamed the far end for what the grep was only
reading about.

Quoting does not disarm everything. Command substitution stays live inside
double quotes, so the parentheses and backticks that open it keep splitting
there, and only single quotes or a backslash make them literal.
"""

import sys
from pathlib import Path

import pytest

HOOKS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HOOKS_ROOT / "common"))

from shell_read_only_inspection_command import (  # noqa: E402
    offset_is_inside_command_substitution,
    offset_lies_in_read_only_inspection_command_segment,
    offset_separates_segments,
    quote_state_by_offset,
    segment_bounds_containing_offset,
)


def offset_of(command_text, needle):
    return command_text.index(needle)


class TestQuoteStateTracking:
    @pytest.mark.parametrize(
        "command_text,needle,expected_state",
        [
            ('grep "a|b" file', "|", '"'),
            ("grep 'a|b' file", "|", "'"),
            ("grep a|b file", "|", ""),
            ("grep a\\|b file", "|", "'"),
            ('echo "one" ; echo "two"', ";", ""),
        ],
    )
    def test_each_offset_carries_the_quote_that_encloses_it(
        self, command_text, needle, expected_state
    ):
        states = quote_state_by_offset(command_text)
        assert states[offset_of(command_text, needle)] == expected_state


class TestSeparatorsInsideQuotes:
    @pytest.mark.parametrize(
        "command_text,needle",
        [
            ('grep "a|b" file', "|"),
            ("grep 'a;b' file", ";"),
            ('echo "one && two"', "&"),
            ("grep a\\;b file", ";"),
        ],
    )
    def test_a_quoted_separator_does_not_split(self, command_text, needle):
        assert not offset_separates_segments(
            command_text, offset_of(command_text, needle)
        )

    @pytest.mark.parametrize(
        "command_text,needle",
        [
            ("grep a file; pytest", ";"),
            ("grep a file | wc -l", "|"),
            ('echo "safe" && pytest', "&"),
        ],
    )
    def test_a_bare_separator_still_splits(self, command_text, needle):
        assert offset_separates_segments(command_text, offset_of(command_text, needle))


class TestCommandSubstitutionSurvivesDoubleQuotes:
    def test_double_quotes_do_not_disarm_a_substitution(self):
        command_text = 'bash -lc "$(cat run.sh)"'
        assert offset_is_inside_command_substitution(
            command_text, offset_of(command_text, "cat")
        )

    def test_single_quotes_make_a_substitution_literal(self):
        command_text = "echo '$(cat run.sh)'"
        assert not offset_is_inside_command_substitution(
            command_text, offset_of(command_text, "cat")
        )


class TestSegmentBounds:
    def test_a_quoted_pipe_keeps_the_grep_in_one_segment(self):
        command_text = 'grep -rn "a\\|b" agents/__tests__/evals/*.py'
        segment_start, segment_end = segment_bounds_containing_offset(
            command_text, offset_of(command_text, "agents")
        )
        assert command_text[segment_start:segment_end] == command_text

    def test_a_bare_separator_still_ends_the_segment(self):
        command_text = "grep -rn a agents; pytest agents/"
        segment_start, segment_end = segment_bounds_containing_offset(
            command_text, offset_of(command_text, "pytest")
        )
        assert command_text[segment_start:segment_end].strip() == "pytest agents/"


class TestTheExemptionItself:
    @pytest.mark.parametrize(
        "command_text,needle",
        [
            ('grep -rn "a\\|b" agents/__tests__/evals/*.py', "__tests__"),
            ("echo 'run __tests__/run.sh in CI; never here'", "__tests__"),
            ("git log --oneline -- 'agents/__tests__/*'", "__tests__"),
        ],
    )
    def test_a_read_only_segment_is_exempt(self, command_text, needle):
        assert offset_lies_in_read_only_inspection_command_segment(
            command_text, offset_of(command_text, needle)
        )

    @pytest.mark.parametrize(
        "command_text,needle",
        [
            ("grep -rn 'a|b' agents; pytest agents/", "pytest"),
            ('bash -lc "$(cat __tests__/run.sh)"', "__tests__"),
            ("echo 'a|b' | bash -c 'pytest agents/'", "pytest"),
            ("cat __tests__/run.sh | bash", "__tests__"),
        ],
    )
    def test_execution_reached_past_a_quoted_separator_is_not_exempt(
        self, command_text, needle
    ):
        assert not offset_lies_in_read_only_inspection_command_segment(
            command_text, offset_of(command_text, needle)
        )
