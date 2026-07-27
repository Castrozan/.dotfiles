import json

from flat_deploy_test_support import (
    CLAWDE_BACKGROUND_AGENT_ENV_MARKER,
    INTERACTIVE_ENV_VAR,
    REMINDER_STATE_DIRECTORY_ENV_VAR,
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)


def test_tldr_reminder_imports_shared_module_after_flat_deploy(tmp_path, monkeypatch):
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENV_MARKER, raising=False)
    flatten_into_single_runtime_directory(tmp_path)

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
    flatten_into_single_runtime_directory(tmp_path)

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
