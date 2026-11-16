from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

BACKGROUND_TASK_ID_IN_RESULT_TEXT = re.compile(r"with ID: ([A-Za-z0-9_-]+)")
OUTPUT_FILE_IN_RESULT_TEXT = re.compile(r"written to: (\S+?\.output)")
NOTIFICATION_FIELD = re.compile(r"<(task-id|tool-use-id)>(.*?)</\1>", re.DOTALL)


@dataclass
class BackgroundCommandRun:
    tool_use_id: str
    tool_name: str
    command: str
    launched_at: datetime
    task_id: str | None = None
    output_file_path: str | None = None
    denied_reason: str | None = None
    first_notified_at: datetime | None = None
    last_seen_running_at: datetime | None = None
    stopped_by_agent_at: datetime | None = None


def timestamp_of(record):
    timestamp_text = record.get("timestamp")
    if not timestamp_text:
        return None
    return datetime.fromisoformat(timestamp_text.replace("Z", "+00:00"))


def _tool_calls_in(record):
    message_content = (record.get("message") or {}).get("content")
    if not isinstance(message_content, list):
        return []
    return [block for block in message_content if isinstance(block, dict)]


def _launches_in_background(tool_name, tool_input):
    return tool_name == "Monitor" or (
        tool_name == "Bash" and tool_input.get("run_in_background") is True
    )


def _launch_from_tool_use(tool_use, record):
    tool_input = tool_use.get("input") or {}
    tool_name = tool_use.get("name")
    launches_in_background = _launches_in_background(tool_name, tool_input)
    launched_at = timestamp_of(record)
    if not launches_in_background or not tool_input.get("command") or not launched_at:
        return None
    return BackgroundCommandRun(
        tool_use_id=tool_use["id"],
        tool_name=tool_name,
        command=tool_input["command"],
        launched_at=launched_at,
    )


def _result_text(tool_result):
    result_content = tool_result.get("content")
    if isinstance(result_content, str):
        return result_content
    if not isinstance(result_content, list):
        return ""
    return "\n".join(
        block.get("text", "") for block in result_content if isinstance(block, dict)
    )
