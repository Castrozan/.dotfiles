from __future__ import annotations

import re
import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in [_MODULE_DIRECTORY] + [
    ancestor / "common" for ancestor in _MODULE_DIRECTORY.parents
]:
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

from hook_dispatch import HandlerResult  # noqa: E402
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
TEST_RUNNER_PATH_PATTERN = rf"{TEST_DIRECTORY_PATTERN}/run\.sh"
TEST_RUNNER_DYNAMIC_PATH_PATTERN = rf"{TEST_DIRECTORY_PATTERN}/[^\s;&|]*[$*?\[{{%`]"
TEST_RUNNER_VARIABLE_PATH_PATTERN = (
    rf"(?=[\s\S]*={TEST_DIRECTORY_PATTERN})(?=[\s\S]*\./\$)"
    rf"(?=[\s\S]*(?:=run\.sh\b|=run(?:[;\s]|$)))"
    rf"(?=[\s\S]*(?:=sh(?:[;\s]|$)|\brun\.sh\b))"
)
TEST_RUNNER_TEMPLATE_PATH_PATTERN = rf"\$\([^;\n]*{TEST_DIRECTORY_PATTERN}/[^;\n]*%"
TEST_RUNNER_AFTER_DIRECTORY_CHANGE_PATTERN = (
    rf"\bcd\s+{TEST_DIRECTORY_PATTERN}\s*(?:&&|;)\s*\./[^;\n]*(?:\brun\.sh\b|`|\$\()"
)
TEST_RUNNER_DENIAL_REASON = (
    "__tests__/run.sh is prohibited locally; CI runs it after push. Run the affected "
    "test file or small named set directly."
)
PYTEST_INVOCATION_PREFIX = r"(?:python3? -m )?pytest\b"
PYTEST_WHOLE_TIER_PATH_TERMINATOR = r"(?:/[*?[]|[\s;&|]|$)"
PYTEST_WHOLE_CI_OWNED_TIER_DIRECTORY_PATTERN = (
    rf"{PYTEST_INVOCATION_PREFIX}[^;&|\n]*?{TEST_DIRECTORY_PATTERN}/"
    rf"(?:unit|integration)/*{PYTEST_WHOLE_TIER_PATH_TERMINATOR}"
)
PYTEST_WHOLE_TESTS_TREE_PATTERN = (
    rf"{PYTEST_INVOCATION_PREFIX}[^;&|\n]*?{TEST_DIRECTORY_PATTERN}/"
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
    "'pytest agents/hooks/__tests__/unit/test_specific_thing.py'."
)
PYTEST_WHOLE_COLLECTION_DENIAL_REASON = (
    "Bare pytest or a whole tests-tree run collects CI-owned tiers; CI runs them "
    "after push. Run a specific test file, for example "
    "'pytest agents/hooks/__tests__/unit/test_specific_thing.py'."
)
MAKE_TEST_SUITE_PATTERN = (
    rf"{COMMAND_INVOCATION_POSITION_PREFIX}make"
    rf"(?:\s+-[^\s]+(?:\s+[^\s]+)?)*\s+test(?:\s|$)"
)
MAKE_TEST_SUITE_DENIAL_REASON = (
    "make test funnels into __tests__/run.sh, which CI runs after push. Run a "
    "specific test file or the affected module's test directly."
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
        MAKE_TEST_SUITE_PATTERN,
        MAKE_TEST_SUITE_DENIAL_REASON,
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
        "herdr agent start without --tab splits an active tab someone is "
        "already working in; --workspace alone is not a pin because it only "
        "chooses which workspace's active tab gets split. Pin the exact tab: "
        '--tab "$HERDR_TAB_ID" --no-focus for your own, or create a fresh one '
        "with 'herdr tab create --workspace <id> --no-focus' and pass its id.",
    ),
    (
        rf"{COMMAND_INVOCATION_POSITION_PREFIX}claude(?![\w-])[^;&|`)\n]*?\s(?:-p|--print)(?:[=\s'\"]|$)",
        "claude -p/--print (headless oneshot) is prohibited; drive an interactive "
        "session instead (the claude-interactive wrapper, or a herdr agent via "
        '\'herdr agent start <name> --cwd <dir> --tab "$HERDR_TAB_ID" --no-focus '
        "-- claude'). "
        "For a genuinely sanctioned one-off, prefix the command with "
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


def extract_inspectable_text(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Bash":
        return tool_input.get("command", "") or ""
    if tool_name == "apply_patch":
        if isinstance(tool_input, str):
            return tool_input
        if isinstance(tool_input, dict):
            return tool_input.get("patch_text", "") or ""
        return ""
    if tool_name in ("Write", "Edit"):
        return tool_input.get("file_path", "") or ""
    if tool_name == "NotebookEdit":
        return (
            tool_input.get("notebook_path", "") or tool_input.get("file_path", "") or ""
        )
    return ""


def find_first_violation(tool_name: str, inspectable_text: str):
    if not inspectable_text:
        return None

    patterns_for_this_tool = PROHIBITED_PATTERNS_BY_TOOL.get(tool_name, [])
    inspection_texts = (inspectable_text,)
    if tool_name == "Bash":
        shell_quote_normalized_text = (
            inspectable_text.replace("\\\n", "")
            .replace("\\", "")
            .replace("'", "")
            .replace('"', "")
        )
        inspection_texts += (
            shell_quote_normalized_text,
            shell_quote_normalized_text.replace("$", ""),
        )

    for rule in patterns_for_this_tool:
        pattern, reason = rule[0], rule[1]
        override_sentinel = rule[2] if len(rule) > 2 else None
        if not any(
            re.search(pattern, candidate_text, re.IGNORECASE)
            for candidate_text in inspection_texts
        ):
            continue
        if override_sentinel and override_sentinel in inspectable_text:
            continue
        return pattern, reason
    return None


def handle(hook_input):
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {}) or {}

    inspectable_text = extract_inspectable_text(tool_name, tool_input)
    violation = find_first_violation(tool_name, inspectable_text)

    if violation is None:
        return None

    _pattern, reason = violation
    block_message = (
        f"BLOCKED ({tool_name}): {reason}\nOffending input: {inspectable_text.strip()}"
    )
    return HandlerResult(
        decision="deny", reason=block_message, system_message=block_message
    )
