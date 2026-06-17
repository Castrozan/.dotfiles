import json
import os
import subprocess
import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
END_OF_TURN_FORMAT_GUARD_SCRIPT = next(HOOKS_ROOT.rglob("end-of-turn-format-guard.py"))

INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER = "CLAWDE_RESUME_FLAG"

WELL_FORMED_REPLY = (
    "The template change and the guard hook are committed and the suite is green.\n"
    "**Done:** rewrote the interactive template and added the stop guard that bounces slop.\n"
    "**Next:** nothing pending"
)


def user_event(text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": text}}


def assistant_text_event(text: str) -> dict:
    return {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


def assistant_tool_use_event() -> dict:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "t1", "name": "Read"}],
        },
    }


def write_transcript_from_events(directory: Path, events: list[dict]) -> Path:
    transcript_path = directory / "transcript.jsonl"
    transcript_path.write_text(
        "\n".join(json.dumps(event) for event in events), encoding="utf-8"
    )
    return transcript_path


def write_transcript_with_final_assistant_reply(
    directory: Path, reply_text: str
) -> Path:
    return write_transcript_from_events(
        directory,
        [
            user_event("hi"),
            assistant_tool_use_event(),
            assistant_text_event(reply_text),
        ],
    )


def invoke_guard(
    payload: dict,
    interactive: bool = True,
    clawde_background_agent: bool = False,
    clawde_marker_value: str = "",
) -> subprocess.CompletedProcess:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key
        not in (
            INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE,
            CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER,
        )
    }
    if interactive:
        environment[INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE] = (
            "/some/interactive-preferences.md"
        )
    if clawde_background_agent:
        environment[CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER] = clawde_marker_value
    return subprocess.run(
        [sys.executable, str(END_OF_TURN_FORMAT_GUARD_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
        env=environment,
    )


def stop_payload(transcript_path: Path, stop_hook_active: bool = False) -> dict:
    return {
        "hook_event_name": "Stop",
        "transcript_path": str(transcript_path),
        "stop_hook_active": stop_hook_active,
    }
