import json
import os
import subprocess
import time
from pathlib import Path

from ab_test_models import SessionTrace, ToolCallEvent


def parse_stream_json_output(
    raw_output: str,
) -> SessionTrace:
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
            message = event.get("message", event)
            content_blocks = message.get("content", [])
            if not isinstance(content_blocks, list):
                continue
            for block in content_blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    trace.tool_calls.append(
                        ToolCallEvent(
                            tool_name=block.get("name", ""),
                            tool_input=block.get("input", {}),
                        )
                    )
                if block.get("type") == "text":
                    text = block.get("text", "")
                    if text.strip():
                        trace.assistant_messages.append(text)

        if event_type == "result":
            result_text = event.get("result", "")
            if isinstance(result_text, str):
                trace.assistant_messages.append(result_text)

    return trace


def run_claude_session_without_system_prompt(
    prompt: str,
    workspace_directory: Path,
    timeout_seconds: int = 120,
    model: str = "haiku",
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
            duration_seconds=time.time() - start_time,
            exit_code=124,
        )

    trace = parse_stream_json_output(result.stdout)
    trace.duration_seconds = time.time() - start_time
    trace.exit_code = result.returncode
    return trace


def run_claude_session_with_system_prompt(
    prompt: str,
    workspace_directory: Path,
    system_prompt: str,
    timeout_seconds: int = 120,
    model: str = "haiku",
) -> SessionTrace:
    command = [
        "claude",
        "-p",
        "--verbose",
        "--output-format",
        "stream-json",
        "--model",
        model,
        "--system-prompt",
        system_prompt,
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
            duration_seconds=time.time() - start_time,
            exit_code=124,
        )

    trace = parse_stream_json_output(result.stdout)
    trace.duration_seconds = time.time() - start_time
    trace.exit_code = result.returncode
    return trace
