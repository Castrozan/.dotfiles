import re

from e2e_models import TerminalSessionTrace, TerminalToolCallEvent

TOOL_CALL_PATTERN = re.compile(r"^[●⬤]\s+(\w+)\((.+)\)\s*$")
TOOL_CALL_MULTILINE_START_PATTERN = re.compile(r"^[●⬤]\s+(\w+)\((.+)$")

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
        stripped_line = line.strip()

        single_line_match = TOOL_CALL_PATTERN.match(stripped_line)
        if single_line_match:
            raw_tool_name = single_line_match.group(1)
            tool_arguments = single_line_match.group(2)
            normalized_tool_name = TOOL_NAME_NORMALIZATION.get(
                raw_tool_name, raw_tool_name
            )
            tool_calls.append(
                TerminalToolCallEvent(
                    tool_name=normalized_tool_name,
                    tool_arguments_text=tool_arguments,
                    position_in_output=line_index,
                )
            )
            continue

        multiline_match = TOOL_CALL_MULTILINE_START_PATTERN.match(stripped_line)
        if multiline_match:
            raw_tool_name = multiline_match.group(1)
            tool_arguments = multiline_match.group(2)
            normalized_tool_name = TOOL_NAME_NORMALIZATION.get(
                raw_tool_name, raw_tool_name
            )
            tool_calls.append(
                TerminalToolCallEvent(
                    tool_name=normalized_tool_name,
                    tool_arguments_text=tool_arguments,
                    position_in_output=line_index,
                )
            )
            continue

        without_bullet = stripped_line.lstrip("●⬤ ")

        if COLLAPSED_READ_PATTERN.match(without_bullet):
            tool_calls.append(
                TerminalToolCallEvent(
                    tool_name="Read",
                    tool_arguments_text=without_bullet,
                    position_in_output=line_index,
                )
            )
            continue

        if COLLAPSED_SEARCH_PATTERN.match(without_bullet):
            tool_calls.append(
                TerminalToolCallEvent(
                    tool_name="Grep",
                    tool_arguments_text=without_bullet,
                    position_in_output=line_index,
                )
            )

    return tool_calls


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
        stripped = line.strip()
        if stripped.startswith("●") or stripped.startswith("⬤"):
            if not TOOL_CALL_PATTERN.match(
                stripped
            ) and not TOOL_CALL_MULTILINE_START_PATTERN.match(stripped):
                text_content = stripped.lstrip("●⬤ ")
                if text_content:
                    text_blocks.append(text_content)

    return text_blocks


def build_terminal_session_trace(
    raw_output: str,
    duration_seconds: float,
    timed_out: bool,
) -> TerminalSessionTrace:
    tool_calls = parse_tool_calls_from_terminal_output(raw_output)
    bash_commands = extract_bash_commands_from_tool_calls(tool_calls)
    assistant_text = extract_assistant_text_from_terminal_output(raw_output)

    return TerminalSessionTrace(
        raw_terminal_output=raw_output,
        detected_tool_calls=tool_calls,
        detected_bash_commands=bash_commands,
        detected_assistant_text_blocks=assistant_text,
        duration_seconds=duration_seconds,
        timed_out=timed_out,
    )


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
        if normalized_skill_name:
            invoked_skill_names.append(normalized_skill_name)
    return invoked_skill_names
