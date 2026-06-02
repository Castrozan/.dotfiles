import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

HOOK_SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "pre-tool-use"
    / "background-bash-anti-pattern-validator.py"
)

_module_spec = importlib.util.spec_from_file_location(
    "background_bash_anti_pattern_validator", HOOK_SCRIPT_PATH
)
sut = importlib.util.module_from_spec(_module_spec)
sys.modules["background_bash_anti_pattern_validator"] = sut
_module_spec.loader.exec_module(sut)


class TestCommandUsesUntilLoopTerminatingOnEmptyCount:
    @pytest.mark.parametrize(
        "command",
        [
            'until [ "$(gh run list --json status --jq length)" = "0" ]; do sleep 15; done',
            'until [ "$(jq length data.json)" = "0" ]; do sleep 5; done',
            'until [ "$(echo 0)" = "0" ]; do sleep 1; done',
            'until [ "$(curl -s api/count | jq .pending)" = 0 ]; do sleep 30; done',
        ],
    )
    def test_flags_until_loop_with_zero_count_termination(self, command):
        assert sut.command_uses_until_loop_terminating_on_empty_count(command) is True

    @pytest.mark.parametrize(
        "command",
        [
            "for i in $(seq 1 60); do sleep 15; done",
            'while [ "$pending" != "" ]; do sleep 5; done',
            "echo hi",
            "sleep 10",
        ],
    )
    def test_passes_non_polling_or_inverted_termination(self, command):
        assert sut.command_uses_until_loop_terminating_on_empty_count(command) is False


class TestCommandFiltersByHardcodedLongLiteralUsedInCountOrTest:
    @pytest.mark.parametrize(
        "command",
        [
            "gh run list --json headSha --jq '[.[] | select(.headSha == \"1e42771447c81fb6a96b2d3eef3e16df9f8517b3\")] | length'",
            "cat data.json | jq '[.[] | select(.id == \"abc12345\")] | length'",
            'echo "$(jq \'select(.branch == "feature/some-branch") | length\' file.json)" = "0"',
        ],
    )
    def test_flags_jq_select_with_long_literal_and_count_test(self, command):
        assert (
            sut.command_filters_by_hardcoded_long_literal_used_in_count_or_test(command)
            is True
        )

    @pytest.mark.parametrize(
        "command",
        [
            "jq --arg sha \"$SHA\" 'select(.headSha == $sha) | length' data.json",
            "jq 'select(.id == \"short\")' file.json",
            "echo hello world",
            "jq 'select(.headSha == \"1e42771447c81fb6a96b2d3eef3e16df9f8517b3\")' file.json",
        ],
    )
    def test_passes_safe_filters_or_no_downstream_count(self, command):
        assert (
            sut.command_filters_by_hardcoded_long_literal_used_in_count_or_test(command)
            is False
        )


class TestCommandPipesCountIntoTestAgainstLiteralZero:
    @pytest.mark.parametrize(
        "command",
        [
            '[ "$(jq length file.json)" = "0" ]',
            '[ "$(gh pr list --json number --jq length)" = "0" ]',
            '[ "$(wc -l < file.txt)" = "0" ]',
            '[ "$(ls | wc -l)" = 0 ]',
        ],
    )
    def test_flags_count_into_test_against_zero(self, command):
        assert sut.command_pipes_count_into_test_against_literal_zero(command) is True

    @pytest.mark.parametrize(
        "command",
        [
            '[ "$(jq length file.json)" -gt "0" ]',
            'matched=$(jq length file.json); [ "$matched" -gt 0 ]',
            'pr_list_json=$(gh pr list --json number); [ "$pr_list_json" = "[]" ]',
        ],
    )
    def test_passes_affirmative_or_inverted_tests(self, command):
        assert sut.command_pipes_count_into_test_against_literal_zero(command) is False


class TestCommandLaunchesInteractiveFullScreenProgram:
    @pytest.mark.parametrize(
        "command",
        [
            "vim notes.txt",
            "vi /etc/hosts",
            "nvim",
            "nano config.ini",
            "top",
            "htop",
            "btop",
            "emacs main.py",
            "EDITOR=vim vim file",
            "sudo vim /etc/sudoers",
            "echo start; vim file",
            "cat data | nano",
        ],
    )
    def test_flags_interactive_editor_or_tui(self, command):
        assert sut.command_launches_interactive_full_screen_program(command) is True

    @pytest.mark.parametrize(
        "command",
        [
            "less /etc/hosts",
            "more file.txt",
            "man ls",
            "echo vim is great",
            "cat vimrc.txt",
            "view-data --top 5",
            "emacs --batch -l build.el",
            "top -l 1",
            "top -b -n1",
            "vim -es -c 'wq' file",
            "nvim --headless -c 'wqa'",
            "python3 -u worker.py",
        ],
    )
    def test_passes_non_interactive_or_unrelated(self, command):
        assert sut.command_launches_interactive_full_screen_program(command) is False


class TestCommandRunsGitSubcommandThatOpensAnEditor:
    @pytest.mark.parametrize(
        "command",
        [
            "git commit",
            "git commit --amend",
            "git add . && git commit",
            "git -c core.editor=vim commit",
            "git rebase -i HEAD~3",
            "git rebase --interactive main",
            "git tag -a v1.0",
            "git tag --annotate release",
        ],
    )
    def test_flags_git_editor_subcommands(self, command):
        assert sut.command_runs_git_subcommand_that_opens_an_editor(command) is True

    @pytest.mark.parametrize(
        "command",
        [
            'git commit -m "feat: x"',
            'git commit -am "fix"',
            "git commit --amend --no-edit",
            "git commit -F message.txt",
            "git commit --message=done",
            "git add -p",
            "git revert --no-commit HEAD",
            "git log --oneline -5",
            "git tag -a v1.0 -m release",
            "git tag v1.0",
            "git status",
        ],
    )
    def test_passes_non_editor_git_invocations(self, command):
        assert sut.command_runs_git_subcommand_that_opens_an_editor(command) is False


class TestBuildDenyReasonMessage:
    def test_hang_rule_message_describes_hang_not_fake_success(self):
        message = sut.build_deny_reason_message(
            ["interactive-editor-or-full-screen-tui"]
        )
        assert "block forever" in message
        assert "exit 0 with empty output" not in message

    def test_mixed_modes_include_both_explanations(self):
        message = sut.build_deny_reason_message(
            [
                "count-piped-into-test-against-zero",
                "git-subcommand-that-opens-an-editor",
            ]
        )
        assert "exit 0 with empty output" in message
        assert "block forever" in message
