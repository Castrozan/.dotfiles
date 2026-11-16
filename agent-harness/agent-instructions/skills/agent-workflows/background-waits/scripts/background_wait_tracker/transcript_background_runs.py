from __future__ import annotations

import json

from .transcript_records import (
    BACKGROUND_TASK_ID_IN_RESULT_TEXT,
    NOTIFICATION_FIELD,
    OUTPUT_FILE_IN_RESULT_TEXT,
    BackgroundCommandRun as BackgroundCommandRun,
    _launch_from_tool_use,
    _result_text,
    _tool_calls_in,
    timestamp_of,
)

API_REQUEST_BLOB_RECORD_PREFIX = b'{"type":"api-request-blob"'


def _structured_task_id(record):
    result = record.get("toolUseResult")
    if isinstance(result, dict):
        return result.get("backgroundTaskId") or result.get("taskId")
    return None


def _is_notification(record, text):
    return (
        record.get("operation") == "enqueue"
        and isinstance(text, str)
        and "<task-notification>" in text
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
                self._collect_stop(tool_use, recorded_at)
                continue
            launch = _launch_from_tool_use(tool_use, record)
            if launch:
                self.runs_by_tool_use_id.setdefault(launch.tool_use_id, launch)

    def _collect_stop(self, tool_use, recorded_at):
        run = self.runs_by_task_id.get((tool_use.get("input") or {}).get("task_id"))
        if run and not run.stopped_by_agent_at:
            run.stopped_by_agent_at = recorded_at

    def _collect_tool_results(self, record):
        for tool_result in _tool_calls_in(record):
            run = self.runs_by_tool_use_id.get(tool_result.get("tool_use_id"))
            if not run or tool_result.get("type") != "tool_result":
                continue
            result_text = _result_text(tool_result)
            if tool_result.get("is_error"):
                run.denied_reason = result_text
                continue
            self._associate_result(run, record, result_text)

    def _associate_result(self, run, record, result_text):
        structured_task_id = _structured_task_id(record)
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
        if not _is_notification(record, notification_text):
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
