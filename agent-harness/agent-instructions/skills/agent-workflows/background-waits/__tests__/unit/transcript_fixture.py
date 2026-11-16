import json
from datetime import datetime, timedelta, timezone

LAUNCH_TIME = datetime(2026, 11, 16, 14, 22, 15, tzinfo=timezone.utc)
PROCESS_SESSION_ID = "process-session-1"

INCIDENT_COMMAND = (
    "first=$(orchestrator report show Reviewer-w4E-p6 2>/dev/null | head -1); n=0; "
    'until { cur=$(orchestrator report show Reviewer-w4E-p6 2>/dev/null | head -1); [ "$cur" != "$first" ]; } '
    "|| [ $n -ge 240 ]; do sleep 45; n=$((n+1)); done; "
    "orchestrator report show Reviewer-w4E-p6"
)


def _timestamp(minutes_after_launch):
    moment = LAUNCH_TIME + timedelta(minutes=minutes_after_launch)
    return moment.isoformat().replace("+00:00", "Z")


def launch_record(tool_use_id, command, tool_name="Bash", minutes_after_launch=0):
    tool_input = {"command": command}
    if tool_name == "Bash":
        tool_input["run_in_background"] = True
    return {
        "type": "assistant",
        "timestamp": _timestamp(minutes_after_launch),
        "session_id": PROCESS_SESSION_ID,
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": tool_use_id,
                    "name": tool_name,
                    "input": tool_input,
                }
            ]
        },
    }


def started_record(tool_use_id, task_id):
    return {
        "type": "user",
        "timestamp": _timestamp(0),
        "session_id": PROCESS_SESSION_ID,
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": (
                        f"Command running in background with ID: {task_id}. Output "
                        f"is being written to: /tmp/tasks/{task_id}.output. You "
                        "will be notified when it completes."
                    ),
                }
            ]
        },
        "toolUseResult": {"backgroundTaskId": task_id},
    }


def denied_record(tool_use_id, reason):
    return {
        "type": "user",
        "timestamp": _timestamp(0),
        "session_id": PROCESS_SESSION_ID,
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": reason,
                    "is_error": True,
                }
            ]
        },
    }


def completion_notification_record(tool_use_id, task_id, minutes_after_launch):
    return {
        "type": "queue-operation",
        "operation": "enqueue",
        "timestamp": _timestamp(minutes_after_launch),
        "content": (
            f"<task-notification>\n<task-id>{task_id}</task-id>\n"
            f"<tool-use-id>{tool_use_id}</tool-use-id>\n"
            "<status>completed</status>\n</task-notification>"
        ),
    }


def monitor_event_record(task_id, minutes_after_launch):
    return {
        "type": "queue-operation",
        "operation": "enqueue",
        "timestamp": _timestamp(minutes_after_launch),
        "content": (
            f"<task-notification>\n<task-id>{task_id}</task-id>\n"
            '<summary>Monitor event: "watch"</summary>\n<event>DONE</event>\n'
            "</task-notification>"
        ),
    }


def task_stop_record(task_id, minutes_after_launch):
    return {
        "type": "assistant",
        "timestamp": _timestamp(minutes_after_launch),
        "session_id": PROCESS_SESSION_ID,
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": f"stop-{task_id}",
                    "name": "TaskStop",
                    "input": {"task_id": task_id},
                }
            ]
        },
    }


def still_running_record(task_id, minutes_after_launch):
    return {
        "type": "attachment",
        "timestamp": _timestamp(minutes_after_launch),
        "session_id": PROCESS_SESSION_ID,
        "attachment": {"type": "task_status", "taskId": task_id, "status": "running"},
    }


def write_transcript(transcript_path, records):
    transcript_path.write_text(
        "".join(json.dumps(record, separators=(",", ":")) + "\n" for record in records)
    )
    return transcript_path
