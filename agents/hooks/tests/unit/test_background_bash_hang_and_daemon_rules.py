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


class TestCommandStartsALingeringDaemonOrService:
    @pytest.mark.parametrize(
        "command",
        [
            "rebuild",
            "rebuild --dry-run",
            "darwin-rebuild switch --flake .",
            "sudo nixos-rebuild switch",
            "home-manager switch -b backup",
            "systemctl start nginx",
            "systemctl --user restart syncthing",
            "launchctl bootstrap gui/501 ~/Library/LaunchAgents/foo.plist",
            "brew services start postgresql",
            "service docker restart",
        ],
    )
    def test_flags_known_daemon_or_service_spawners(self, command):
        assert sut.command_starts_a_lingering_daemon_or_service(command) is True

    @pytest.mark.parametrize(
        "command",
        [
            "echo rebuilding the index",
            "systemctl status nginx",
            "systemctl stop nginx",
            "brew services list",
            "git rebuild-cache",
            "make rebuild-docs",
        ],
    )
    def test_passes_non_service_starting_commands(self, command):
        assert sut.command_starts_a_lingering_daemon_or_service(command) is False


class TestLingeringDaemonAdvisory:
    def test_advisory_message_points_to_detach_wrapper(self):
        message = sut.build_lingering_daemon_advisory_message()
        assert "launch-command-detached-into-new-session" in message
        assert "process group" in message
