import re
from pathlib import Path

from e2e.sessions.e2e_models import TerminalSessionTrace, TerminalToolCallEvent
from e2e.sessions.e2e_session_transcript import (
    assistant_messages_from_session_transcript,
    tool_calls_from_session_transcript,
)

TOOL_CALL_PATTERN = re.compile(r"^[●⬤⏺]\s+(\w+)\((.+)\)\s*$")
TOOL_CALL_MULTILINE_START_PATTERN = re.compile(r"^[●⬤⏺]\s+(\w+)\((.+)$")

TOOL_NAME_NORMALIZATION = {
    "Update": "Edit",
    "Bash": "Bash",
    "Read": "Read",
    "Write": "Write",
    "Glob": "Glob",
    "Grep": "Grep",
    "Skill": "Skill",
    "Agent": "Agent",
    "ToolSearch": "ToolSearch",
}

ASSISTANT_TEXT_BULLETS = ("●", "⬤", "⏺")
COLLAPSED_BASH_ARGUMENTS_TEXT = "<collapsed by the transcript>"
COLLAPSED_SHELL_RUN_PATTERN = re.compile(r"^Ran (\d+) shell commands?$")
COLLAPSED_READ_PATTERN = re.compile(r"^\s*(?:Read|Reading) \d+ file")
COLLAPSED_SEARCH_PATTERN = re.compile(r"^\s*Searched for \d+ pattern")
COLLAPSED_LISTED_PATTERN = re.compile(
    r"^\s*(?:Read|Reading) \d+ file|[Ll]isted \d+ director"
)


def parse_tool_calls_from_terminal_output(
    raw_output: str,
) -> list[TerminalToolCallEvent]:
    tool_calls = []
    lines = raw_output.split("\n")

    for line_index, line in enumerate(lines):
        tool_calls.extend(_tool_calls_from_terminal_line(line.strip(), line_index))

    return tool_calls


def _tool_calls_from_terminal_line(
    stripped_line: str, line_index: int
) -> list[TerminalToolCallEvent]:
    single_line_match = TOOL_CALL_PATTERN.match(stripped_line)
    if single_line_match:
        return [_terminal_tool_call(single_line_match, line_index)]
    multiline_match = TOOL_CALL_MULTILINE_START_PATTERN.match(stripped_line)
    if multiline_match:
        return [_terminal_tool_call(multiline_match, line_index)]
    return _collapsed_tool_calls(stripped_line.lstrip("●⬤⏺ "), line_index)


def _terminal_tool_call(match, line_index):
    raw_tool_name = match.group(1)
    return TerminalToolCallEvent(
        tool_name=TOOL_NAME_NORMALIZATION.get(raw_tool_name, raw_tool_name),
        tool_arguments_text=match.group(2),
        position_in_output=line_index,
    )


def _collapsed_tool_calls(
    without_bullet: str, line_index: int
) -> list[TerminalToolCallEvent]:
    if COLLAPSED_READ_PATTERN.match(without_bullet):
        return [_collapsed_tool_call("Read", without_bullet, line_index)]
    if COLLAPSED_SEARCH_PATTERN.match(without_bullet):
        return [_collapsed_tool_call("Grep", without_bullet, line_index)]
    collapsed_shell_run = COLLAPSED_SHELL_RUN_PATTERN.match(without_bullet)
    if collapsed_shell_run:
        return [
            _collapsed_tool_call("Bash", COLLAPSED_BASH_ARGUMENTS_TEXT, line_index)
            for _ in range(int(collapsed_shell_run.group(1)))
        ]
    return []


def _collapsed_tool_call(tool_name: str, arguments: str, line_index: int):
    return TerminalToolCallEvent(
        tool_name=tool_name,
        tool_arguments_text=arguments,
        position_in_output=line_index,
    )


def extract_bash_commands_from_tool_calls(
    tool_calls: list[TerminalToolCallEvent],
) -> list[str]:
    return [tc.tool_arguments_text for tc in tool_calls if tc.tool_name == "Bash"]


def extract_assistant_text_from_terminal_output(
    raw_output: str,
) -> list[str]:
    text_blocks = []
    lines = raw_output.split("\n")

    for line in lines:
        text_block = _assistant_text_block(line.strip())
        if text_block:
            text_blocks.append(text_block)

    return text_blocks


def _assistant_text_block(stripped: str) -> str:
    if not stripped.startswith(ASSISTANT_TEXT_BULLETS):
        return ""
    if TOOL_CALL_PATTERN.match(stripped) or TOOL_CALL_MULTILINE_START_PATTERN.match(
        stripped
    ):
        return ""
    return stripped.lstrip("●⬤⏺ ")


def build_terminal_session_trace(
    raw_output: str,
    duration_seconds: float,
    timed_out: bool,
    workspace: Path | None = None,
) -> TerminalSessionTrace:
    tool_calls = _trace_tool_calls(raw_output, workspace)
    bash_commands = extract_bash_commands_from_tool_calls(tool_calls)
    assistant_text = _trace_assistant_text(raw_output, workspace)

    return TerminalSessionTrace(
        raw_terminal_output=raw_output,
        detected_tool_calls=tool_calls,
        detected_bash_commands=bash_commands,
        detected_assistant_text_blocks=assistant_text,
        duration_seconds=duration_seconds,
        timed_out=timed_out,
    )


def _trace_tool_calls(raw_output: str, workspace: Path | None):
    tool_calls = (
        tool_calls_from_session_transcript(workspace) if workspace is not None else []
    )
    return tool_calls or parse_tool_calls_from_terminal_output(raw_output)


def _trace_assistant_text(raw_output: str, workspace: Path | None):
    assistant_text = (
        assistant_messages_from_session_transcript(workspace)
        if workspace is not None
        else []
    )
    return assistant_text or extract_assistant_text_from_terminal_output(raw_output)


def extract_tool_name_sequence(
    trace: TerminalSessionTrace,
) -> list[str]:
    return [tc.tool_name for tc in trace.detected_tool_calls]


def extract_invoked_skill_names_from_trace(
    trace: TerminalSessionTrace,
) -> list[str]:
    invoked_skill_names = []
    for tool_call in trace.detected_tool_calls:
        if tool_call.tool_name != "Skill":
            continue
        first_argument_token = tool_call.tool_arguments_text.split(",")[0].strip()
        normalized_skill_name = first_argument_token.strip("\"'").strip()
        unqualified_skill_name = normalized_skill_name.rpartition(":")[2]
        if unqualified_skill_name:
            invoked_skill_names.append(unqualified_skill_name)
    return invoked_skill_names
