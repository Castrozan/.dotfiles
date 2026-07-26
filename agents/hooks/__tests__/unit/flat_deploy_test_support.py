import json
import shutil
import subprocess
import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
USER_PROMPT_SUBMIT_DISPATCHER_SOURCE = next(
    HOOKS_ROOT.rglob("user-prompt-submit-dispatcher.py")
)
TLDR_REMINDER_HANDLER_SOURCE = next(HOOKS_ROOT.rglob("tldr_reminder_handler.py"))
HOOK_DISPATCH_SOURCE = HOOKS_ROOT / "common" / "hook_dispatch.py"
STOP_DISPATCHER_SOURCE = next(HOOKS_ROOT.rglob("stop-dispatcher.py"))
END_OF_TURN_FORMAT_GUARD_HANDLER_SOURCE = next(
    HOOKS_ROOT.rglob("end_of_turn_format_guard_handler.py")
)
LINT_TURN_REVIEW_HANDLER_SOURCE = next(HOOKS_ROOT.rglob("lint_turn_review_handler.py"))
LINT_LEDGER_SOURCE = next(HOOKS_ROOT.rglob("lint_ledger.py"))
LINTER_TABLE_BY_EXTENSION_SOURCE = next(
    HOOKS_ROOT.rglob("linter_table_by_extension.py")
)
REPO_NATIVE_LINT_COMMAND_DETECTION_SOURCE = next(
    HOOKS_ROOT.rglob("repo_native_lint_command_detection.py")
)
INTERACTIVE_SESSION_DETECTION_SOURCE = (
    HOOKS_ROOT / "common" / "interactive_session_detection.py"
)
END_OF_TURN_REPLY_TEMPLATE_RULES_SOURCE = next(
    HOOKS_ROOT.rglob("end_of_turn_reply_template_rules.py")
)
REPLY_TEMPLATE_SHAPE_AND_LENGTH_RULES_SOURCE = next(
    HOOKS_ROOT.rglob("reply_template_shape_and_length_rules.py")
)
INTERACTIVE_REPLY_REMINDER_STATE_SOURCE = (
    HOOKS_ROOT / "common" / "interactive_reply_reminder_state.py"
)
POST_TOOL_USE_DISPATCHER_SOURCE = next(HOOKS_ROOT.rglob("post-tool-use-dispatcher.py"))
AUTO_FORMAT_HANDLER_SOURCE = next(HOOKS_ROOT.rglob("auto_format_handler.py"))
NIX_REBUILD_TRIGGER_HANDLER_SOURCE = next(
    HOOKS_ROOT.rglob("nix_rebuild_trigger_handler.py")
)
RECORD_EDITED_SOURCE_FILE_HANDLER_SOURCE = next(
    HOOKS_ROOT.rglob("record_edited_source_file_handler.py")
)
LINE_COUNT_LIMIT_GUARD_HANDLER_SOURCE = next(
    HOOKS_ROOT.rglob("line_count_limit_guard_handler.py")
)
RECORD_INSTRUCTIONS_SKILL_INVOCATION_HANDLER_SOURCE = next(
    HOOKS_ROOT.rglob("record_instructions_skill_invocation_handler.py")
)
CHANGED_FILE_PATHS_SOURCE = HOOKS_ROOT / "common" / "changed_file_paths.py"
FORMATTER_TABLE_BY_EXTENSION_SOURCE = next(
    HOOKS_ROOT.rglob("formatter_table_by_extension.py")
)
LINE_COUNT_POLICY_SOURCE = next(HOOKS_ROOT.rglob("line_count_policy.py"))
LINE_COUNT_BLOCK_MESSAGE_SOURCE = next(HOOKS_ROOT.rglob("line-count-block-message.md"))
INSTRUCTIONS_SKILL_MARKER_SOURCE = (
    HOOKS_ROOT / "common" / "instructions_skill_marker.py"
)

INTERACTIVE_ENV_VAR = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENV_MARKER = "CLAWDE_RESUME_FLAG"
REMINDER_STATE_DIRECTORY_ENV_VAR = "INTERACTIVE_REPLY_REMINDER_STATE_DIRECTORY"


def flatten_into_single_runtime_directory(directory, source_files):
    for source_file in source_files:
        shutil.copy(source_file, directory / source_file.name)


def run_flattened_hook(directory, hook_filename, payload, environment):
    return subprocess.run(
        [sys.executable, str(directory / hook_filename)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
        env=environment,
    )
