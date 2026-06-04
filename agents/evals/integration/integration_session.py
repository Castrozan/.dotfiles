import json
import os
import subprocess
import time
from pathlib import Path

from integration_models import SessionTrace, ToolCallEvent


def extract_tool_calls_from_assistant_message(
    message_data: dict,
) -> list[ToolCallEvent]:
    extracted_tool_calls = []
    message = message_data.get("message", message_data)
    content_blocks = message.get("content", [])

    if not isinstance(content_blocks, list):
        return extracted_tool_calls

    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "tool_use":
            extracted_tool_calls.append(
                ToolCallEvent(
                    tool_name=block.get("name", ""),
                    tool_input=block.get("input", {}),
                    timestamp=time.time(),
                )
            )

    return extracted_tool_calls


def extract_text_from_assistant_message(
    message_data: dict,
) -> str | None:
    message = message_data.get("message", message_data)
    content_blocks = message.get("content", [])

    if not isinstance(content_blocks, list):
        return None

    text_parts = []
    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text_content = block.get("text", "")
            if text_content.strip():
                text_parts.append(text_content)

    return " ".join(text_parts) if text_parts else None


def parse_stream_json_output(raw_output: str) -> SessionTrace:
    trace = SessionTrace()

    for line in raw_output.strip().split("\n"):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type", "")

        if event_type == "assistant":
            tool_calls = extract_tool_calls_from_assistant_message(event)
            trace.tool_calls.extend(tool_calls)

            text_content = extract_text_from_assistant_message(event)
            if text_content:
                trace.assistant_messages.append(text_content)

        if event_type == "result":
            result_text = event.get("result", "")
            if isinstance(result_text, str) and result_text.strip():
                trace.assistant_messages.append(result_text)

    return trace


def extract_tool_name_sequence(
    trace: SessionTrace,
) -> list[str]:
    return [tool_call.tool_name for tool_call in trace.tool_calls]


def collect_written_file_content_from_tool_calls(
    trace: SessionTrace,
) -> str:
    written_content_parts = []
    for tool_call in trace.tool_calls:
        if tool_call.tool_name in ("Edit", "Write"):
            new_string = tool_call.tool_input.get("new_string", "")
            content = tool_call.tool_input.get("content", "")
            if new_string:
                written_content_parts.append(new_string)
            if content:
                written_content_parts.append(content)
    return "\n".join(written_content_parts)


def run_claude_session(
    prompt: str,
    workspace_directory: Path,
    timeout_seconds: int = 180,
    model: str = "sonnet",
) -> SessionTrace:
    command = [
        "claude",
        "-p",
        "--verbose",
        "--output-format",
        "stream-json",
        "--model",
        model,
        prompt,
    ]

    start_time = time.time()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=workspace_directory,
            timeout=timeout_seconds,
            env={
                key: value for key, value in os.environ.items() if key != "CLAUDECODE"
            },
        )
    except subprocess.TimeoutExpired:
        return SessionTrace(
            full_output=(f"Session timed out after {timeout_seconds}s"),
            duration_seconds=time.time() - start_time,
            exit_code=124,
        )

    duration = time.time() - start_time
    trace = parse_stream_json_output(result.stdout)
    trace.full_output = result.stdout + result.stderr
    trace.duration_seconds = duration
    trace.exit_code = result.returncode
    return trace
