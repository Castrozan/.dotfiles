import re
import subprocess
import sys
from pathlib import Path

VOLUME_ICONS_DIR = Path.home() / ".config" / "scripts" / "icons"
VOLUME_STEP_NORMAL = 5
VOLUME_STEP_PRECISE = 1


def find_active_sink_name_or_default() -> str:
    default_sink_name = subprocess.run(
        ["pactl", "get-default-sink"],
        capture_output=True,
        text=True,
    ).stdout.strip()

    sinks_output = subprocess.run(
        ["pactl", "list", "sinks", "short"],
        capture_output=True,
        text=True,
    ).stdout

    for line in sinks_output.splitlines():
        fields = line.split("\t")
        if (
            len(fields) >= 7
            and fields[1] == default_sink_name
            and fields[6] == "RUNNING"
        ):
            return default_sink_name

    for line in sinks_output.splitlines():
        fields = line.split("\t")
        if len(fields) >= 7 and fields[6] == "RUNNING":
            return fields[1]

    return "@DEFAULT_SINK@"


def get_volume_for_active_sink() -> int:
    sink_name = find_active_sink_name_or_default()
    result = subprocess.run(
        ["pactl", "get-sink-volume", sink_name],
        capture_output=True,
        text=True,
    )
    match = re.search(r"(\d+)%", result.stdout)
    return int(match.group(1)) if match else 0


def is_sink_muted() -> bool:
    sink_name = find_active_sink_name_or_default()
    result = subprocess.run(
        ["pactl", "get-sink-mute", sink_name],
        capture_output=True,
        text=True,
    )
    return "yes" in result.stdout


def get_volume_icon_path() -> str:
    current_volume = get_volume_for_active_sink()
    if is_sink_muted() or current_volume == 0:
        return str(VOLUME_ICONS_DIR / "volume-mute.png")
    if current_volume <= 30:
        return str(VOLUME_ICONS_DIR / "volume-low.png")
    if current_volume <= 60:
        return str(VOLUME_ICONS_DIR / "volume-mid.png")
    return str(VOLUME_ICONS_DIR / "volume-high.png")


def send_volume_osd() -> None:
    current_volume = get_volume_for_active_sink()
    subprocess.run(["quickshell-osd-send", "volume", str(current_volume)])


def increase_volume(step: int) -> None:
    sink_name = find_active_sink_name_or_default()
    subprocess.run(
        ["pactl", "set-sink-volume", sink_name, f"+{step}%"],
        capture_output=True,
    )
    send_volume_osd()


def decrease_volume(step: int) -> None:
    sink_name = find_active_sink_name_or_default()
    subprocess.run(
        ["pactl", "set-sink-volume", sink_name, f"-{step}%"],
        capture_output=True,
    )
    send_volume_osd()


def toggle_mute() -> None:
    sink_name = find_active_sink_name_or_default()
    subprocess.run(
        ["pactl", "set-sink-mute", sink_name, "toggle"],
        capture_output=True,
    )
    if is_sink_muted():
        subprocess.run(["quickshell-osd-send", "mute", "true"])
    else:
        send_volume_osd()


def increase_microphone_volume(step: int) -> None:
    subprocess.run(
        ["pactl", "set-source-volume", "@DEFAULT_SOURCE@", f"+{step}%"],
        capture_output=True,
    )
    send_microphone_osd()


def decrease_microphone_volume(step: int) -> None:
    subprocess.run(
        ["pactl", "set-source-volume", "@DEFAULT_SOURCE@", f"-{step}%"],
        capture_output=True,
    )
    send_microphone_osd()


def toggle_microphone_mute() -> None:
    subprocess.run(
        ["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"],
        capture_output=True,
    )
    result = subprocess.run(
        ["pactl", "get-source-mute", "@DEFAULT_SOURCE@"],
        capture_output=True,
        text=True,
    )
    if "yes" in result.stdout:
        subprocess.run(["quickshell-osd-send", "mic-mute", "true"])
    else:
        send_microphone_osd()


def send_microphone_osd() -> None:
    result = subprocess.run(
        ["pactl", "get-source-volume", "@DEFAULT_SOURCE@"],
        capture_output=True,
        text=True,
    )
    match = re.search(r"(\d+)%", result.stdout)
    current_volume = int(match.group(1)) if match else 0
    subprocess.run(["quickshell-osd-send", "mic", str(current_volume)])


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "--get"

    match action:
        case "--inc":
            increase_volume(VOLUME_STEP_NORMAL)
        case "--dec":
            decrease_volume(VOLUME_STEP_NORMAL)
        case "--inc-precise":
            increase_volume(VOLUME_STEP_PRECISE)
        case "--dec-precise":
            decrease_volume(VOLUME_STEP_PRECISE)
        case "--toggle":
            toggle_mute()
        case "--toggle-mic":
            toggle_microphone_mute()
        case "--mic-inc":
            increase_microphone_volume(VOLUME_STEP_NORMAL)
        case "--mic-dec":
            decrease_microphone_volume(VOLUME_STEP_NORMAL)
        case "--send-osd":
            send_volume_osd()
        case "--get":
            print(get_volume_for_active_sink())
        case "--get-icon":
            print(get_volume_icon_path())
        case "--get-mic-icon":
            print(VOLUME_ICONS_DIR / "microphone.png")
        case _:
            print(get_volume_for_active_sink())


if __name__ == "__main__":
    main()
