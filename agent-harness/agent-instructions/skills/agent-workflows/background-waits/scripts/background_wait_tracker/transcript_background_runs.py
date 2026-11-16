from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime

API_REQUEST_BLOB_RECORD_PREFIX = b'{"type":"api-request-blob"'
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


def _launch_from_tool_use(tool_use, record):
    tool_input = tool_use.get("input") or {}
    tool_name = tool_use.get("name")
    launches_in_background = tool_name == "Monitor" or (
        tool_name == "Bash" and tool_input.get("run_in_background") is True
    )
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


class TranscriptBackgroundRunCollector:
    def __init__(self):
        self.runs_by_tool_use_id = {}
        self.runs_by_task_id = {}

    def collect(self, record):
        record_type = record.get("type")
        recorded_at = timestamp_of(record)
        if record_type == "assistant":
            self._collect_tool_uses(record, recorded_at)
        elif record_type == "user":
            self._collect_tool_results(record)
        elif record_type == "queue-operation":
            self._collect_notification(record, recorded_at)
        elif record_type == "attachment":
            self._collect_task_status(record, recorded_at)

    def _collect_tool_uses(self, record, recorded_at):
        for tool_use in _tool_calls_in(record):
            if tool_use.get("type") != "tool_use":
                continue
            if tool_use.get("name") == "TaskStop":
                stopped_run = self.runs_by_task_id.get(
                    (tool_use.get("input") or {}).get("task_id")
                )
                if stopped_run and not stopped_run.stopped_by_agent_at:
                    stopped_run.stopped_by_agent_at = recorded_at
                continue
            launch = _launch_from_tool_use(tool_use, record)
            if launch:
                self.runs_by_tool_use_id.setdefault(launch.tool_use_id, launch)

    def _collect_tool_results(self, record):
        for tool_result in _tool_calls_in(record):
            run = self.runs_by_tool_use_id.get(tool_result.get("tool_use_id"))
            if not run or tool_result.get("type") != "tool_result":
                continue
            result_text = _result_text(tool_result)
            if tool_result.get("is_error"):
                run.denied_reason = result_text
                continue
            structured_result = record.get("toolUseResult")
            structured_task_id = (
                structured_result.get("backgroundTaskId")
                or structured_result.get("taskId")
                if isinstance(structured_result, dict)
                else None
            )
            task_id_in_text = BACKGROUND_TASK_ID_IN_RESULT_TEXT.search(result_text)
            run.task_id = structured_task_id or (
                task_id_in_text.group(1) if task_id_in_text else None
            )
            output_file = OUTPUT_FILE_IN_RESULT_TEXT.search(result_text)
            run.output_file_path = output_file.group(1) if output_file else None
            if run.task_id:
                self.runs_by_task_id[run.task_id] = run

    def _collect_notification(self, record, recorded_at):
        notification_text = record.get("content")
        if (
            record.get("operation") != "enqueue"
            or not isinstance(notification_text, str)
            or "<task-notification>" not in notification_text
        ):
            return
        fields = dict(NOTIFICATION_FIELD.findall(notification_text))
        run = self.runs_by_tool_use_id.get(
            fields.get("tool-use-id")
        ) or self.runs_by_task_id.get(fields.get("task-id"))
        if not run:
            return
        if not run.first_notified_at:
            run.first_notified_at = recorded_at

    def _collect_task_status(self, record, recorded_at):
        attachment = record.get("attachment") or {}
        run = self.runs_by_task_id.get(attachment.get("taskId"))
        if (
            run
            and attachment.get("type") == "task_status"
            and attachment.get("status") == "running"
        ):
            run.last_seen_running_at = recorded_at

    def collected_runs(self):
        return list(self.runs_by_tool_use_id.values())


def background_command_runs_in_transcript(transcript_path):
    collector = TranscriptBackgroundRunCollector()
    with open(transcript_path, "rb") as transcript_file:
        for raw_record in transcript_file:
            if raw_record.startswith(API_REQUEST_BLOB_RECORD_PREFIX):
                continue
            try:
                record = json.loads(raw_record)
            except ValueError:
                continue
            if isinstance(record, dict):
                collector.collect(record)
    return collector.collected_runs()
