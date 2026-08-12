from __future__ import annotations

import os
import sys

_MODULE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
_ANCESTOR_DIRECTORY = _MODULE_DIRECTORY
_SHARED_MODULE_CANDIDATE_DIRECTORIES = [_MODULE_DIRECTORY]
while _ANCESTOR_DIRECTORY != os.path.dirname(_ANCESTOR_DIRECTORY):
    _ANCESTOR_DIRECTORY = os.path.dirname(_ANCESTOR_DIRECTORY)
    _SHARED_MODULE_CANDIDATE_DIRECTORIES.append(
        os.path.join(_ANCESTOR_DIRECTORY, "common")
    )
for _shared_module_candidate_directory in _SHARED_MODULE_CANDIDATE_DIRECTORIES:
    if (
        os.path.isdir(_shared_module_candidate_directory)
        and _shared_module_candidate_directory not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_directory)

from shell_command_invocation_position import (  # noqa: E402
    COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD,
    COMMAND_INVOCATION_POSITION_PREFIX,
)

SANCTIONED_HEADLESS_CLAUDE_OVERRIDE_SENTINEL = "CLAUDE_HEADLESS_SANCTIONED=1"
TEST_DIRECTORY_PATTERN = (
    r"(?:__tests__|__test[*?@\[][^\s/]*|__tes[*?@\[][^\s/]*|"
    r"__te[*?@\[][^\s/]*|__t[*?@\[][^\s/]*|__[*?@\[][^\s/]*|"
    r"[*?@\[][^\s/]*tests__)"
)
TEST_RUNNER_DIRECTORY_PATTERN = rf"(?:{TEST_DIRECTORY_PATTERN}|repository/verification)"
TEST_RUNNER_PATH_PATTERN = rf"{TEST_RUNNER_DIRECTORY_PATTERN}/run\.sh"
TEST_RUNNER_DYNAMIC_PATH_PATTERN = (
    rf"{TEST_RUNNER_DIRECTORY_PATTERN}/[^\s;&|]*[$*?\[{{%`]"
)
TEST_RUNNER_VARIABLE_PATH_PATTERN = (
    rf"(?=[\s\S]*={TEST_RUNNER_DIRECTORY_PATTERN})(?=[\s\S]*\./\$)"
    rf"(?=[\s\S]*(?:=run\.sh\b|=run(?:[;\s]|$)))"
    rf"(?=[\s\S]*(?:=sh(?:[;\s]|$)|\brun\.sh\b))"
)
TEST_RUNNER_TEMPLATE_PATH_PATTERN = (
    rf"\$\([^;\n]*{TEST_RUNNER_DIRECTORY_PATTERN}/[^;\n]*%"
)
TEST_RUNNER_AFTER_DIRECTORY_CHANGE_PATTERN = rf"\bcd\s+{TEST_RUNNER_DIRECTORY_PATTERN}\s*(?:&&|;)\s*\./[^;\n]*(?:\brun\.sh\b|`|\$\()"
TEST_RUNNER_DENIAL_REASON = (
    "repository/verification/run.sh is prohibited locally; CI runs it after push. Run the affected "
    "test file or small named set directly."
)
PYTEST_INVOCATION_PREFIX = r"(?:python3? -m )?pytest\b"
PYTEST_WHOLE_TIER_PATH_TERMINATOR = r"(?:/[*?[]|[\s;&|]|$)"
PYTEST_CI_OWNED_TREE_ROOT_PATTERN = (
    rf"(?:{TEST_DIRECTORY_PATTERN}|agent-harness/quality/evaluations)"
)
PYTEST_WHOLE_CI_OWNED_TIER_DIRECTORY_PATTERN = (
    rf"{PYTEST_INVOCATION_PREFIX}[^;&|\n]*?{PYTEST_CI_OWNED_TREE_ROOT_PATTERN}/"
    rf"(?:unit|integration)/*{PYTEST_WHOLE_TIER_PATH_TERMINATOR}"
)
PYTEST_WHOLE_TESTS_TREE_PATTERN = (
    rf"{PYTEST_INVOCATION_PREFIX}[^;&|\n]*?{PYTEST_CI_OWNED_TREE_ROOT_PATTERN}/"
    rf"*{PYTEST_WHOLE_TIER_PATH_TERMINATOR}"
)
PYTEST_NO_PATH_PATTERN = (
    rf"{PYTEST_INVOCATION_PREFIX}(?!\s+--?(?:version|help|fixtures)\b)(?!\s+-h\b)"
    rf"(?:\s+(?:-\S+(?:\s+\S+)?|\S+=\S+))*\s*(?:[;&|]|$)"
)
PYTEST_DOT_PATH_PATTERN = rf"{PYTEST_INVOCATION_PREFIX}\s+\.(?:/\.|/)?(?:\s|$|[;&|])"
PYTEST_AGENTS_TREE_PATTERN = (
    rf"{PYTEST_INVOCATION_PREFIX}[^;&|\n]*?\bagents\b/?"
    rf"(?:\s+-\S+(?:\s+\S+)?)*\s*(?:[;&|]|$)"
)
PYTEST_CI_OWNED_TIER_DENIAL_REASON = (
    "pytest over a whole CI-owned tier directory is prohibited; CI runs the unit "
    "and integration tiers after push. Run a specific test file, for example "
    "'pytest agent-harness/hooks/runtime/__tests__/unit/test_specific_thing.py'."
)
PYTEST_WHOLE_COLLECTION_DENIAL_REASON = (
    "Bare pytest or a whole tests-tree run collects CI-owned tiers; CI runs them "
    "after push. Run a specific test file, for example "
    "'pytest agent-harness/hooks/runtime/__tests__/unit/test_specific_thing.py'."
)
NIX_FLAKE_CHECK_PATTERN = (
    rf"{COMMAND_INVOCATION_POSITION_PREFIX}nix\s+flake\s+check"
    rf"(?!\s+--?(?:help|version)\b)(?:\s|$|[;&|])"
)
NIX_FLAKE_CHECK_DENIAL_REASON = (
    "nix flake check runs in CI after push; the local verification for a nix "
    "change is 'rebuild'."
)

PROHIBITED_BASH_COMMAND_PATTERNS = [
    (
        TEST_RUNNER_PATH_PATTERN,
        TEST_RUNNER_DENIAL_REASON,
    ),
    (
        PYTEST_WHOLE_CI_OWNED_TIER_DIRECTORY_PATTERN,
        PYTEST_CI_OWNED_TIER_DENIAL_REASON,
    ),
    (
        PYTEST_WHOLE_TESTS_TREE_PATTERN,
        PYTEST_WHOLE_COLLECTION_DENIAL_REASON,
    ),
    (
        TEST_RUNNER_DYNAMIC_PATH_PATTERN,
        TEST_RUNNER_DENIAL_REASON,
    ),
    (
        TEST_RUNNER_VARIABLE_PATH_PATTERN,
        TEST_RUNNER_DENIAL_REASON,
    ),
    (
        TEST_RUNNER_TEMPLATE_PATH_PATTERN,
        TEST_RUNNER_DENIAL_REASON,
    ),
    (
        TEST_RUNNER_AFTER_DIRECTORY_CHANGE_PATTERN,
        TEST_RUNNER_DENIAL_REASON,
    ),
    (
        PYTEST_NO_PATH_PATTERN,
        PYTEST_WHOLE_COLLECTION_DENIAL_REASON,
    ),
    (
        PYTEST_DOT_PATH_PATTERN,
        PYTEST_WHOLE_COLLECTION_DENIAL_REASON,
    ),
    (
        PYTEST_AGENTS_TREE_PATTERN,
        PYTEST_WHOLE_COLLECTION_DENIAL_REASON,
    ),
    (
        NIX_FLAKE_CHECK_PATTERN,
        NIX_FLAKE_CHECK_DENIAL_REASON,
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}git\s+add\s+"
        rf"(?:-A|--all|\.){COMMAND_ARGUMENT_TERMINATOR_LOOKAHEAD}",
        "git add -A/--all/. is prohibited; stage specific files (parallel work risk).",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}(?:git|gh\s+repo)\s+clone\s+\S*castrozan[/-]?\.?dotfiles",
        "Cloning castrozan/.dotfiles is prohibited; use 'gh api' for remote access.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}direnv\s+(allow|hook|exec|reload|status|edit|deny|block|prune|version)\b",
        "direnv is prohibited; use 'devenv shell' or 'devenv shell -- command'.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}herdr\s+agent\s+start\b(?:(?!\s--tab(?=[\s=]))(?!\s--\s)[^;&|\n])*(?:$|[;&|\n]|\s--\s)",
        "herdr agent start without --tab splits an active tab someone is already "
        "working in, and --workspace alone is not a pin. Pin the exact tab with "
        "--tab and pass --no-focus; the herdr skill carries the recipe.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}herdr\s+(?:workspace|tab|pane)\s+close\b",
        "herdr workspace/tab/pane close is prohibited; no close can prove it owns "
        "its target and there is no undo. Leave what you spawned for the human to "
        "close, and read the herdr skill's knowledge for why the id lies.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}claude(?![\w-])[^;&|`)\n]*?\s(?:-p|--print)(?:[=\s'\"]|$)",
        "claude -p/--print (headless oneshot) is prohibited; drive an interactive "
        "session instead, through the claude-interactive wrapper or a herdr agent "
        "as the herdr skill describes. A sanctioned one-off needs the prefix "
        f"{SANCTIONED_HEADLESS_CLAUDE_OVERRIDE_SENTINEL}.",
        SANCTIONED_HEADLESS_CLAUDE_OVERRIDE_SENTINEL,
    ),
]

PROHIBITED_FILE_PATH_PATTERNS = [
    (
        r"(?:^|[\s/])castrozan/\.?dotfiles(?:/|$)",
        "Writing under castrozan/.dotfiles is prohibited; repo must not live on disk.",
    ),
]

PROHIBITED_PATTERNS_BY_TOOL = {
    "Bash": PROHIBITED_BASH_COMMAND_PATTERNS,
    "Write": PROHIBITED_FILE_PATH_PATTERNS,
    "Edit": PROHIBITED_FILE_PATH_PATTERNS,
    "NotebookEdit": PROHIBITED_FILE_PATH_PATTERNS,
    "apply_patch": PROHIBITED_FILE_PATH_PATTERNS,
}
