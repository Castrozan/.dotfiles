"""A heredoc body is data, unless the command it feeds runs what it reads.

Writing a commit message that quotes a prohibited command was denied as if the
message were the command. The body of a heredoc is stdin for the command that
opened it, so for git commit, gh issue create or cat it is inert text, and the
guards that forbid RUNNING something have nothing to forbid there.

The exception is the command that executes its input. A body fed to bash, sh
or python is a script, and piping an inert body into one of those is the same
thing by another route.
"""

import sys
from pathlib import Path

import pytest

HOOKS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HOOKS_ROOT / "common"))

from shell_heredoc_body import (  # noqa: E402
    inert_heredoc_body_bounds,
    offset_lies_in_inert_heredoc_body,
)

COMMIT_MESSAGE_QUOTING_A_PROHIBITED_COMMAND = (
    "git commit -F- -- agent-harness/hooks/runtime <<'MESSAGE'\n"
    "fix(hooks): stop denying a message that mentions the suite\n"
    "\n"
    "Running repository/verification/run.sh locally stays prohibited.\n"
    "MESSAGE"
)

SCRIPT_FED_TO_AN_INTERPRETER = (
    "bash <<'EOF'\nrepository/verification/run.sh --quick\nEOF"
)

INERT_BODY_PIPED_INTO_AN_INTERPRETER = (
    "cat <<'EOF' | bash\nrepository/verification/run.sh --quick\nEOF"
)


def offset_of(command_text, needle):
    return command_text.index(needle)


class TestAnInertBodyIsNotExecutedText:
    @pytest.mark.parametrize(
        "command_text,needle",
        [
            (COMMIT_MESSAGE_QUOTING_A_PROHIBITED_COMMAND, "repository"),
            (
                "gh issue create --body-file - <<'BODY'\npytest agents/ is CI-only\nBODY",
                "pytest",
            ),
            ("cat <<'NOTE' > notes.md\nmake test is CI-owned\nNOTE", "make test"),
        ],
    )
    def test_the_body_of_a_heredoc_a_plain_command_reads_is_inert(
        self, command_text, needle
    ):
        assert offset_lies_in_inert_heredoc_body(
            command_text, offset_of(command_text, needle)
        )

    def test_the_opener_line_itself_is_not_part_of_the_body(self):
        command_text = COMMIT_MESSAGE_QUOTING_A_PROHIBITED_COMMAND
        assert not offset_lies_in_inert_heredoc_body(
            command_text, offset_of(command_text, "git commit")
        )

    def test_the_body_ends_at_its_delimiter_line(self):
        command_text = "cat <<'EOF'\ninside\nEOF\npytest agents/"
        assert not offset_lies_in_inert_heredoc_body(
            command_text, offset_of(command_text, "pytest")
        )


class TestABodyAnInterpreterReadsIsAScript:
    @pytest.mark.parametrize(
        "command_text",
        [
            SCRIPT_FED_TO_AN_INTERPRETER,
            INERT_BODY_PIPED_INTO_AN_INTERPRETER,
            "sudo bash <<'EOF'\nrepository/verification/run.sh\nEOF",
            "python3 <<'EOF'\nrepository/verification/run.sh\nEOF",
        ],
    )
    def test_a_body_that_gets_executed_is_never_inert(self, command_text):
        assert not offset_lies_in_inert_heredoc_body(
            command_text, offset_of(command_text, "repository")
        )


class TestBoundsReporting:
    def test_a_command_without_a_heredoc_reports_no_bounds(self):
        assert inert_heredoc_body_bounds("grep -rn thing agents") == []

    def test_an_unterminated_body_runs_to_the_end_of_the_command(self):
        command_text = "cat <<'EOF'\nstill inside"
        body_start, body_end = inert_heredoc_body_bounds(command_text)[0]
        assert command_text[body_start:body_end] == "still inside"
