import json

from flat_deploy_test_support import (
    AUTO_FORMAT_HANDLER_SOURCE,
    CHANGED_FILE_PATHS_SOURCE,
    FORMATTER_TABLE_BY_EXTENSION_SOURCE,
    HOOK_DISPATCH_SOURCE,
    INSTRUCTIONS_SKILL_MARKER_SOURCE,
    LINE_COUNT_BLOCK_MESSAGE_SOURCE,
    LINE_COUNT_LIMIT_GUARD_HANDLER_SOURCE,
    LINE_COUNT_POLICY_SOURCE,
    LINT_LEDGER_SOURCE,
    LINTER_TABLE_BY_EXTENSION_SOURCE,
    NIX_REBUILD_TRIGGER_HANDLER_SOURCE,
    POST_TOOL_USE_DISPATCHER_SOURCE,
    RECORD_EDITED_SOURCE_FILE_HANDLER_SOURCE,
    RECORD_INSTRUCTIONS_SKILL_INVOCATION_HANDLER_SOURCE,
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)


def test_post_tool_use_dispatcher_imports_shared_modules_after_flat_deploy(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(
        runtime_directory,
        [
            POST_TOOL_USE_DISPATCHER_SOURCE,
            AUTO_FORMAT_HANDLER_SOURCE,
            NIX_REBUILD_TRIGGER_HANDLER_SOURCE,
            RECORD_EDITED_SOURCE_FILE_HANDLER_SOURCE,
            LINE_COUNT_LIMIT_GUARD_HANDLER_SOURCE,
            RECORD_INSTRUCTIONS_SKILL_INVOCATION_HANDLER_SOURCE,
            HOOK_DISPATCH_SOURCE,
            CHANGED_FILE_PATHS_SOURCE,
            FORMATTER_TABLE_BY_EXTENSION_SOURCE,
            LINT_LEDGER_SOURCE,
            LINTER_TABLE_BY_EXTENSION_SOURCE,
            LINE_COUNT_POLICY_SOURCE,
            LINE_COUNT_BLOCK_MESSAGE_SOURCE,
            INSTRUCTIONS_SKILL_MARKER_SOURCE,
        ],
    )

    over_threshold_file = tmp_path / "too_long.py"
    over_threshold_file.write_text("\n".join(f"line_{n}" for n in range(250)) + "\n")
    blocked = run_flattened_hook(
        runtime_directory,
        "post-tool-use-dispatcher.py",
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": str(over_threshold_file)},
        },
        {"TMPDIR": str(tmp_path)},
    )
    assert blocked.returncode == 0
    payload = json.loads(blocked.stdout)
    assert payload["decision"] == "block"
