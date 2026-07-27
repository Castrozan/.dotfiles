import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

worktree_location_guard_handler = import_hyphenated_hook_module(
    "worktree_location_guard_handler"
)


def guard(command):
    return worktree_location_guard_handler.handle(
        {"tool_name": "Bash", "tool_input": {"command": command}}
    )


def test_blocks_a_sibling_directory_worktree():
    result = guard("git worktree add ../feature-branch -b feature-branch")
    assert result is not None
    assert result.decision == "deny"
    assert ".worktrees/" in result.reason


def test_blocks_a_bare_name_that_lands_beside_the_repository():
    result = guard("git worktree add wt-feature -b feature")
    assert result is not None
    assert result.decision == "deny"


def test_blocks_an_absolute_path_outside_the_repository():
    result = guard("git worktree add /Users/someone/dotfiles-arr -b arr")
    assert result is not None
    assert result.decision == "deny"


def test_blocks_a_home_relative_path():
    result = guard("git worktree add ~/repo/wt-thing -b thing")
    assert result is not None
    assert result.decision == "deny"


def test_allows_the_gitignored_in_repository_convention():
    assert guard("git worktree add .worktrees/feature -b feature") is None


def test_allows_the_built_in_claude_worktrees_directory():
    assert guard("git worktree add .claude/worktrees/feature -b feature") is None


def test_allows_an_absolute_path_inside_a_repository_worktrees_directory():
    assert (
        guard("git worktree add /Users/someone/.dotfiles/.worktrees/feature -b feature")
        is None
    )


def test_finds_the_destination_past_leading_flags():
    result = guard("git worktree add --detach --force ../elsewhere")
    assert result is not None
    assert result.decision == "deny"
    result = guard("git worktree add -b feature .worktrees/feature")
    assert result is None


def test_reads_through_a_git_directory_override():
    result = guard("git -C /Users/someone/other-repo worktree add ../elsewhere")
    assert result is not None
    assert result.decision == "deny"


def test_ignores_other_worktree_subcommands():
    assert guard("git worktree list") is None
    assert guard("git worktree remove ../old-tree") is None
    assert guard("git worktree move ../old-tree .worktrees/old-tree") is None
    assert guard("git worktree prune") is None


def test_ignores_commands_that_are_not_worktree_creation():
    assert guard("git add .worktrees/feature") is None
    assert guard("echo git worktree add ../elsewhere") is None


def test_a_sanctioned_override_lets_an_outside_worktree_through():
    sentinel = worktree_location_guard_handler.OUTSIDE_REPOSITORY_OVERRIDE_SENTINEL
    assert guard(f"{sentinel} git worktree add ../elsewhere -b elsewhere") is None


def test_ignores_tools_other_than_bash():
    assert (
        worktree_location_guard_handler.handle(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": "git worktree add ../elsewhere"},
            }
        )
        is None
    )


def test_names_the_offending_destination_in_the_denial():
    result = guard("git worktree add ../feature-branch")
    assert "../feature-branch" in result.reason
