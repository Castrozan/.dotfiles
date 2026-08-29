import json
import os
import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2] / "scripts" / "notify_codex_turn_complete.py"
)


def create_notify_send_recorder(tmp_path: Path) -> tuple[Path, Path]:
    notification_log_path = tmp_path / "notification.log"
    notify_send_path = tmp_path / "notify-send"
    notify_send_path.write_text(
        '#!/usr/bin/env bash\nprintf "%s\\n" "$@" > "$NOTIFICATION_LOG_PATH"\n',
        encoding="utf-8",
    )
    notify_send_path.chmod(0o755)
    return notify_send_path, notification_log_path


def run_notifier(
    tmp_path: Path, payload: str, working_directory: Path | None = None
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    notify_send_path, notification_log_path = create_notify_send_recorder(tmp_path)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(notify_send_path), payload],
        capture_output=True,
        text=True,
        cwd=working_directory,
        env=os.environ | {"NOTIFICATION_LOG_PATH": str(notification_log_path)},
    )
    notification_arguments = (
        notification_log_path.read_text(encoding="utf-8").splitlines()
        if notification_log_path.exists()
        else []
    )
    return result, notification_arguments


def test_turn_completion_uses_the_request_as_title_and_result_as_body(tmp_path):
    payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "input-messages": ["Check every ARR container and report health"],
            "last-assistant-message": "All 11 ARR containers remain\n  running.",
        }
    )

    result, notification_arguments = run_notifier(tmp_path, payload)

    assert result.returncode == 0, result.stderr
    assert notification_arguments == [
        "--app-name",
        "Codex",
        "Codex · Check every ARR container and report health",
        "All 11 ARR containers remain running.",
    ]


def test_missing_event_text_falls_back_to_the_working_directory(tmp_path):
    project_directory = tmp_path / "dotfiles"
    project_directory.mkdir()
    payload = json.dumps({"type": "agent-turn-complete"})

    result, notification_arguments = run_notifier(
        tmp_path, payload, working_directory=project_directory
    )

    assert result.returncode == 0, result.stderr
    assert notification_arguments[-2:] == [
        "Codex · dotfiles",
        "Turn complete",
    ]


def test_long_event_text_is_bounded(tmp_path):
    payload = json.dumps(
        {
            "type": "agent-turn-complete",
            "input-messages": ["request " * 30],
            "last-assistant-message": "result " * 100,
        }
    )

    result, notification_arguments = run_notifier(tmp_path, payload)

    assert result.returncode == 0, result.stderr
    assert len(notification_arguments[-2]) <= 100
    assert len(notification_arguments[-1]) <= 320
    assert notification_arguments[-2].endswith("…")
    assert notification_arguments[-1].endswith("…")


def test_malformed_or_unknown_events_do_not_notify(tmp_path):
    for payload in ("not-json", json.dumps({"type": "approval-requested"})):
        result, notification_arguments = run_notifier(tmp_path, payload)

        assert result.returncode == 0, result.stderr
        assert notification_arguments == []
