import os
import signal
import subprocess
import sys
from pathlib import Path

NOTIFICATION_SOUNDS_MUTE_FLAG = Path.home() / ".cache" / "notification-sounds-muted"
NOTIFICATION_SOUND_MONITOR_PID_FILE = (
    Path.home() / ".cache" / "notification-sound-monitor.pid"
)
NOTIFICATION_SOUND_DAEMON_PID_FILE = (
    Path.home() / ".cache" / "notification-sound-daemon.pid"
)
NOTIFICATION_SOUND_FILE = "/usr/share/sounds/freedesktop/stereo/message-new-instant.oga"


def is_notification_sounds_muted() -> bool:
    return NOTIFICATION_SOUNDS_MUTE_FLAG.is_file()


def is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def read_pid_from_file(pid_file: Path) -> int | None:
    if not pid_file.is_file():
        return None
    try:
        return int(pid_file.read_text().strip())
    except (ValueError, OSError):
        return None


def is_notification_sound_monitor_running() -> bool:
    pid = read_pid_from_file(NOTIFICATION_SOUND_MONITOR_PID_FILE)
    return pid is not None and is_pid_running(pid)


def mute_notification_sink_inputs() -> None:
    result = subprocess.run(
        ["pactl", "list", "sink-inputs"],
        capture_output=True,
        text=True,
    )

    current_index = None
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("Sink Input #"):
            current_index = stripped.split("#")[1]
        elif current_index and (
            'media.role = "event"' in stripped
            or 'media.role = "notification"' in stripped
            or 'media.role = "alert"' in stripped
            or "anberra" in stripped
        ):
            subprocess.run(
                [
                    "pactl",
                    "set-sink-input-mute",
                    current_index,
                    "1",
                ],
                capture_output=True,
            )
            current_index = None


def stop_process_by_pid_file(pid_file: Path) -> None:
    pid = read_pid_from_file(pid_file)
    if pid is None:
        return
    try:
        subprocess.run(["pkill", "-P", str(pid)], capture_output=True)
        os.kill(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass
    pid_file.unlink(missing_ok=True)


def start_notification_sound_monitor() -> None:
    stop_process_by_pid_file(NOTIFICATION_SOUND_MONITOR_PID_FILE)

    mute_flag_path = str(NOTIFICATION_SOUNDS_MUTE_FLAG)
    monitor_script = (
        f'trap "exit 0" TERM HUP\n'
        f"pactl subscribe 2>/dev/null "
        f"| while read -r subscribeEvent; do\n"
        f'  if [[ "$subscribeEvent" == *"\'new\' on sink-input"* ]] '
        f'&& [[ -f "{mute_flag_path}" ]]; then\n'
        f'    newSinkInputIndex=$(echo "$subscribeEvent" '
        f'| grep -oP "#\\\\K\\\\d+" || true)\n'
        f'    [[ -z "$newSinkInputIndex" ]] && continue\n'
        f"    sleep 0.05\n"
        f"    sinkInputProperties=$(pactl list sink-inputs 2>/dev/null "
        f'| sed -n "/^Sink Input #${{newSinkInputIndex}}$/'
        f',/^Sink Input #/p" || true)\n'
        f'    if echo "$sinkInputProperties" '
        f"| grep -qiE "
        f"'media\\\\.role = \"(event|notification|alert)\"' "
        f"|| \\\\\n"
        f'       echo "$sinkInputProperties" '
        f"| grep -qiE "
        f"'application\\\\.name = \".*[Cc]anberra\"'; then\n"
        f'      pactl set-sink-input-mute "$newSinkInputIndex" '
        f"1 2>/dev/null || true\n"
        f"    fi\n"
        f"  fi\n"
        f"done\n"
    )
    process = subprocess.Popen(
        ["bash", "-c", monitor_script],
        start_new_session=True,
    )
    NOTIFICATION_SOUND_MONITOR_PID_FILE.write_text(str(process.pid))


def stop_notification_sound_monitor() -> None:
    stop_process_by_pid_file(NOTIFICATION_SOUND_MONITOR_PID_FILE)


def ensure_notification_sound_monitor_running() -> None:
    if is_notification_sounds_muted() and not is_notification_sound_monitor_running():
        start_notification_sound_monitor()


def is_notification_sound_daemon_running() -> bool:
    pid = read_pid_from_file(NOTIFICATION_SOUND_DAEMON_PID_FILE)
    return pid is not None and is_pid_running(pid)


def start_notification_sound_daemon() -> None:
    stop_process_by_pid_file(NOTIFICATION_SOUND_DAEMON_PID_FILE)

    mute_flag_path = str(NOTIFICATION_SOUNDS_MUTE_FLAG)
    sound_file = NOTIFICATION_SOUND_FILE
    daemon_script = (
        f'trap "exit 0" TERM HUP\n'
        f"dbus-monitor --session --monitor "
        f"\"interface='org.freedesktop.Notifications',"
        f"member='Notify',"
        f"type='method_call'\" "
        f"2>/dev/null | while read -r dbusLine; do\n"
        f'  if [[ "$dbusLine" == *"member=Notify"* ]] '
        f'&& [[ ! -f "{mute_flag_path}" ]]; then\n'
        f'    paplay "{sound_file}" 2>/dev/null &\n'
        f"  fi\n"
        f"done\n"
    )
    process = subprocess.Popen(
        ["bash", "-c", daemon_script],
        start_new_session=True,
    )
    NOTIFICATION_SOUND_DAEMON_PID_FILE.write_text(str(process.pid))


def stop_notification_sound_daemon() -> None:
    stop_process_by_pid_file(NOTIFICATION_SOUND_DAEMON_PID_FILE)


def ensure_notification_sound_daemon_running() -> None:
    if not is_notification_sound_daemon_running():
        start_notification_sound_daemon()


def toggle_notification_sounds() -> None:
    if is_notification_sounds_muted():
        NOTIFICATION_SOUNDS_MUTE_FLAG.unlink(missing_ok=True)
        stop_notification_sound_monitor()
    else:
        NOTIFICATION_SOUNDS_MUTE_FLAG.touch()
        mute_notification_sink_inputs()
        start_notification_sound_monitor()


def notification_sound_status() -> None:
    ensure_notification_sound_daemon_running()
    ensure_notification_sound_monitor_running()
    if is_notification_sounds_muted():
        print('{"text":"󰂛","tooltip":"Notification sounds: OFF","class":"muted"}')
    else:
        print('{"text":"󰂚","tooltip":"Notification sounds: ON","class":"on"}')


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    match action:
        case "toggle":
            toggle_notification_sounds()
        case "status":
            notification_sound_status()
        case _:
            print(
                "Usage: hypr-notification-sound-toggle {toggle|status}",
                file=sys.stderr,
            )
            raise SystemExit(1)


if __name__ == "__main__":
    main()
