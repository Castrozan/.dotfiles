import json
import re
from pathlib import Path

from e2e.sessions.e2e_models import TerminalToolCallEvent

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
    if tool_name == "Skill":
        return str(tool_input.get("skill", ""))
    return json.dumps(tool_input, sort_keys=True)


def tool_calls_from_session_transcript(
    workspace: Path,
) -> list[TerminalToolCallEvent]:
    transcript = newest_session_transcript_file(workspace)
    if transcript is None:
        return []

    return [
        tool_call
        for position, line in enumerate(transcript.read_text().splitlines())
        for tool_call in _tool_calls_from_transcript_line(line, position)
    ]


def _tool_calls_from_transcript_line(line: str, position: int):
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        return []
    content = (entry.get("message") or {}).get("content")
    if not isinstance(content, list):
        return []
    return [
        TerminalToolCallEvent(
            tool_name=block.get("name", ""),
            tool_arguments_text=tool_call_argument_text(
                block.get("name", ""), block.get("input") or {}
            ),
            position_in_output=position,
        )
        for block in content
        if _is_tool_use_block(block)
    ]


def _is_tool_use_block(block):
    return isinstance(block, dict) and block.get("type") == "tool_use"


def assistant_messages_from_session_transcript(workspace: Path) -> list[str]:
    transcript = newest_session_transcript_file(workspace)
    if transcript is None:
        return []
    return [
        message
        for line in transcript.read_text().splitlines()
        if (message := _assistant_message_from_transcript_line(line))
    ]


def _assistant_message_from_transcript_line(line: str) -> str:
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        return ""
    content = _assistant_content(entry)
    return _assistant_text(content)


def _assistant_content(entry):
    message = entry.get("message") or {}
    if message.get("role") != "assistant":
        return None
    content = message.get("content")
    return content if isinstance(content, list) else None


def _assistant_text(content):
    if content is None:
        return ""
    return "".join(
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    ).strip()
