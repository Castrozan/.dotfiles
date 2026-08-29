import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "codex_turn_notification"
    / "notify.py"
)


@dataclass(frozen=True)
class NotifierRun:
    result: subprocess.CompletedProcess[str]
    notification_arguments: list[str]
    desktop_focus_log_path: Path
    herdr_log_path: Path


def create_notification_recorder(tmp_path: Path) -> tuple[Path, Path]:
    notification_log_path = tmp_path / "notification.log"
    notification_executable_path = tmp_path / "notification-executable"
    notification_executable_path.write_text(
        "#!/usr/bin/env bash\n"
        'printf "%s\\n" "$@" > "$NOTIFICATION_LOG_PATH"\n'
        'printf "%s" "${NOTIFICATION_ACTION:-}"\n',
        encoding="utf-8",
    )
    notification_executable_path.chmod(0o755)
    return notification_executable_path, notification_log_path


def create_desktop_focus_recorder(tmp_path: Path, platform: str) -> tuple[Path, Path]:
    desktop_focus_log_path = tmp_path / "desktop-focus.log"
    desktop_focus_path = tmp_path / "desktop-focus"
    command_body = (
        'if [ "$*" = "-j activeworkspace" ]; then printf "%s" "$ACTIVE_WORKSPACE_JSON"; exit; fi\n'
        'if [ "$*" = "-j clients" ]; then printf "%s" "$HYPRLAND_CLIENTS_JSON"; exit; fi\n'
        if platform == "linux"
        else ""
    )
    desktop_focus_path.write_text(
        "#!/usr/bin/env bash\n"
        + command_body
        + 'printf "%s\\n" "$@" > "$DESKTOP_FOCUS_LOG_PATH"\n',
        encoding="utf-8",
    )
    desktop_focus_path.chmod(0o755)
    return desktop_focus_path, desktop_focus_log_path


def create_herdr_recorder(tmp_path: Path) -> tuple[Path, Path]:
    herdr_log_path = tmp_path / "herdr.log"
    herdr_path = tmp_path / "herdr"
    herdr_path.write_text(
        "#!/usr/bin/env bash\n"
        'if [ "$*" = "agent list" ]; then printf "%s" "$HERDR_AGENT_LIST_JSON"; exit; fi\n'
        'printf "%s\\n" "$@" > "$HERDR_LOG_PATH"\n',
        encoding="utf-8",
    )
    herdr_path.chmod(0o755)
    return herdr_path, herdr_log_path


def run_notifier(
    tmp_path: Path,
    payload: str,
    platform: str = "linux",
    working_directory: Path | None = None,
    environment: dict[str, str] | None = None,
) -> NotifierRun:
    notification_executable_path, notification_log_path = create_notification_recorder(
        tmp_path
    )
    desktop_focus_path, desktop_focus_log_path = create_desktop_focus_recorder(
        tmp_path, platform
    )
    herdr_path, herdr_log_path = create_herdr_recorder(tmp_path)
    command_environment = (
        os.environ
        | {
            "ACTIVE_WORKSPACE_JSON": '{"id": 11}',
            "DESKTOP_FOCUS_LOG_PATH": str(desktop_focus_log_path),
            "HERDR_AGENT_LIST_JSON": '{"result":{"agents":[]}}',
            "HERDR_LOG_PATH": str(herdr_log_path),
            "HYPRLAND_CLIENTS_JSON": "[]",
            "NOTIFICATION_LOG_PATH": str(notification_log_path),
        }
        | (environment or {})
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            platform,
            str(notification_executable_path),
            str(desktop_focus_path),
            str(herdr_path),
            payload,
        ],
        capture_output=True,
        text=True,
        cwd=working_directory,
        env=command_environment,
    )
    notification_arguments = (
        notification_log_path.read_text(encoding="utf-8").splitlines()
        if notification_log_path.exists()
        else []
    )
    return NotifierRun(
        result,
        notification_arguments,
        desktop_focus_log_path,
        herdr_log_path,
    )
