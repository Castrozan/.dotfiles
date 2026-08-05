import json
import re
from pathlib import Path

from e2e_models import TerminalToolCallEvent

SESSION_TRANSCRIPT_ROOT = Path.home() / ".claude" / "projects"
NON_ALPHANUMERIC = re.compile(r"[^a-zA-Z0-9]")


def claude_project_directory_for_workspace(workspace: Path) -> Path:
    return SESSION_TRANSCRIPT_ROOT / NON_ALPHANUMERIC.sub("-", str(workspace))


def newest_session_transcript_file(workspace: Path) -> Path | None:
    project_directory = claude_project_directory_for_workspace(workspace)
    transcripts = sorted(
        project_directory.glob("*.jsonl"), key=lambda path: path.stat().st_mtime
    )
    return transcripts[-1] if transcripts else None


def tool_call_argument_text(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Bash":
        return str(tool_input.get("command", ""))
    return json.dumps(tool_input, sort_keys=True)


def tool_calls_from_session_transcript(
    workspace: Path,
) -> list[TerminalToolCallEvent]:
    transcript = newest_session_transcript_file(workspace)
    if transcript is None:
        return []

    tool_calls = []
    for position, line in enumerate(transcript.read_text().splitlines()):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        content = (entry.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            tool_name = block.get("name", "")
            tool_calls.append(
                TerminalToolCallEvent(
                    tool_name=tool_name,
                    tool_arguments_text=tool_call_argument_text(
                        tool_name, block.get("input") or {}
                    ),
                    position_in_output=position,
                )
            )
    return tool_calls
