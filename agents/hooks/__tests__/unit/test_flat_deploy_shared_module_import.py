import json

from flat_deploy_test_support import (
    CLAWDE_BACKGROUND_AGENT_ENV_MARKER,
    END_OF_TURN_FORMAT_GUARD_HANDLER_SOURCE,
    END_OF_TURN_REPLY_TEMPLATE_RULES_SOURCE,
    HOOK_DISPATCH_SOURCE,
    INTERACTIVE_ENV_VAR,
    INTERACTIVE_REPLY_REMINDER_STATE_SOURCE,
    INTERACTIVE_SESSION_DETECTION_SOURCE,
    LINT_LEDGER_SOURCE,
    LINT_TURN_REVIEW_HANDLER_SOURCE,
    LINTER_TABLE_BY_EXTENSION_SOURCE,
    REMINDER_STATE_DIRECTORY_ENV_VAR,
    REPLY_TEMPLATE_SHAPE_AND_LENGTH_RULES_SOURCE,
    REPO_NATIVE_LINT_COMMAND_DETECTION_SOURCE,
    STOP_DISPATCHER_SOURCE,
    TLDR_REMINDER_HANDLER_SOURCE,
    USER_PROMPT_SUBMIT_DISPATCHER_SOURCE,
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)


def test_tldr_reminder_imports_shared_module_after_flat_deploy(tmp_path, monkeypatch):
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENV_MARKER, raising=False)
    flatten_into_single_runtime_directory(
        tmp_path,
        [
            USER_PROMPT_SUBMIT_DISPATCHER_SOURCE,
            TLDR_REMINDER_HANDLER_SOURCE,
            HOOK_DISPATCH_SOURCE,
            INTERACTIVE_SESSION_DETECTION_SOURCE,
            INTERACTIVE_REPLY_REMINDER_STATE_SOURCE,
        ],
    )

    keyboard = run_flattened_hook(
        tmp_path,
        "user-prompt-submit-dispatcher.py",
        {"hook_event_name": "UserPromptSubmit", "session_id": "flat-deploy"},
        {
            INTERACTIVE_ENV_VAR: "/some/interactive-preferences.md",
            REMINDER_STATE_DIRECTORY_ENV_VAR: str(tmp_path),
        },
    )
    assert keyboard.returncode == 0
    assert (
        "Done:"
        in json.loads(keyboard.stdout)["hookSpecificOutput"]["additionalContext"]
    )

    clawde = run_flattened_hook(
        tmp_path,
        "user-prompt-submit-dispatcher.py",
        {"hook_event_name": "UserPromptSubmit", "session_id": "flat-deploy"},
        {
            INTERACTIVE_ENV_VAR: "/some/interactive-preferences.md",
            REMINDER_STATE_DIRECTORY_ENV_VAR: str(tmp_path),
            CLAWDE_BACKGROUND_AGENT_ENV_MARKER: "",
        },
    )
    assert clawde.returncode == 0
    assert clawde.stdout.strip() == ""


def test_stop_dispatcher_imports_shared_modules_after_flat_deploy(
    tmp_path, monkeypatch
):
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENV_MARKER, raising=False)
    flatten_into_single_runtime_directory(
        tmp_path,
        [
            STOP_DISPATCHER_SOURCE,
            END_OF_TURN_FORMAT_GUARD_HANDLER_SOURCE,
            LINT_TURN_REVIEW_HANDLER_SOURCE,
            HOOK_DISPATCH_SOURCE,
            INTERACTIVE_SESSION_DETECTION_SOURCE,
            END_OF_TURN_REPLY_TEMPLATE_RULES_SOURCE,
            REPLY_TEMPLATE_SHAPE_AND_LENGTH_RULES_SOURCE,
            INTERACTIVE_REPLY_REMINDER_STATE_SOURCE,
            LINT_LEDGER_SOURCE,
            LINTER_TABLE_BY_EXTENSION_SOURCE,
            REPO_NATIVE_LINT_COMMAND_DETECTION_SOURCE,
        ],
    )

    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        "\n".join(
            json.dumps(event)
            for event in [
                {"type": "user", "message": {"role": "user", "content": "hi"}},
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": "You're right — done.\n**Done:** x\n**Next:** y",
                            }
                        ],
                    },
                },
            ]
        ),
        encoding="utf-8",
    )
    payload = {
        "hook_event_name": "Stop",
        "transcript_path": str(transcript),
        "stop_hook_active": False,
        "session_id": "flat-deploy-stop",
    }

    keyboard = run_flattened_hook(
        tmp_path,
        "stop-dispatcher.py",
        payload,
        {
            INTERACTIVE_ENV_VAR: "/some/interactive-preferences.md",
            REMINDER_STATE_DIRECTORY_ENV_VAR: str(tmp_path),
        },
    )
    assert keyboard.returncode == 0
    assert json.loads(keyboard.stdout)["decision"] == "block"

    clawde = run_flattened_hook(
        tmp_path,
        "stop-dispatcher.py",
        payload,
        {
            INTERACTIVE_ENV_VAR: "/some/interactive-preferences.md",
            REMINDER_STATE_DIRECTORY_ENV_VAR: str(tmp_path),
            CLAWDE_BACKGROUND_AGENT_ENV_MARKER: "",
        },
    )
    assert clawde.returncode == 0
    assert clawde.stdout.strip() == ""
