import json
import shutil
import subprocess
import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
TLDR_REMINDER_SOURCE = next(HOOKS_ROOT.rglob("tldr-reminder.py"))
END_OF_TURN_FORMAT_GUARD_SOURCE = next(HOOKS_ROOT.rglob("end-of-turn-format-guard.py"))
INTERACTIVE_SESSION_DETECTION_SOURCE = (
    HOOKS_ROOT / "common" / "interactive_session_detection.py"
)
END_OF_TURN_REPLY_TEMPLATE_RULES_SOURCE = next(
    HOOKS_ROOT.rglob("end_of_turn_reply_template_rules.py")
)

INTERACTIVE_ENV_VAR = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENV_MARKER = "CLAWDE_RESUME_FLAG"


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


def test_tldr_reminder_imports_shared_module_after_flat_deploy(tmp_path, monkeypatch):
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENV_MARKER, raising=False)
    flatten_into_single_runtime_directory(
        tmp_path, [TLDR_REMINDER_SOURCE, INTERACTIVE_SESSION_DETECTION_SOURCE]
    )

    keyboard = run_flattened_hook(
        tmp_path,
        "tldr-reminder.py",
        {"hook_event_name": "UserPromptSubmit"},
        {INTERACTIVE_ENV_VAR: "/some/interactive-preferences.md"},
    )
    assert keyboard.returncode == 0
    assert (
        "Done:"
        in json.loads(keyboard.stdout)["hookSpecificOutput"]["additionalContext"]
    )

    clawde = run_flattened_hook(
        tmp_path,
        "tldr-reminder.py",
        {"hook_event_name": "UserPromptSubmit"},
        {
            INTERACTIVE_ENV_VAR: "/some/interactive-preferences.md",
            CLAWDE_BACKGROUND_AGENT_ENV_MARKER: "",
        },
    )
    assert clawde.returncode == 0
    assert clawde.stdout.strip() == ""


def test_format_guard_imports_shared_module_after_flat_deploy(tmp_path, monkeypatch):
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENV_MARKER, raising=False)
    flatten_into_single_runtime_directory(
        tmp_path,
        [
            END_OF_TURN_FORMAT_GUARD_SOURCE,
            INTERACTIVE_SESSION_DETECTION_SOURCE,
            END_OF_TURN_REPLY_TEMPLATE_RULES_SOURCE,
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
    }

    keyboard = run_flattened_hook(
        tmp_path,
        "end-of-turn-format-guard.py",
        payload,
        {INTERACTIVE_ENV_VAR: "/some/interactive-preferences.md"},
    )
    assert keyboard.returncode == 0
    assert json.loads(keyboard.stdout)["decision"] == "block"

    clawde = run_flattened_hook(
        tmp_path,
        "end-of-turn-format-guard.py",
        payload,
        {
            INTERACTIVE_ENV_VAR: "/some/interactive-preferences.md",
            CLAWDE_BACKGROUND_AGENT_ENV_MARKER: "",
        },
    )
    assert clawde.returncode == 0
    assert clawde.stdout.strip() == ""
