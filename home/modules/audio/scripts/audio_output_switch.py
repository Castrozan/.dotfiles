import subprocess
from pathlib import Path

AUDIO_OUTPUT_ICONS_DIR = Path.home() / ".config" / "scripts" / "icons"


def list_all_hardware_sink_names() -> list[str]:
    result = subprocess.run(
        ["pactl", "list", "sinks", "short"],
        capture_output=True,
        text=True,
    )
    sinks = []
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) >= 2 and not fields[1].endswith(".monitor"):
            sinks.append(fields[1])
    return sinks


def find_next_sink_in_cycle(sink_names: list[str], current_sink: str) -> str:
    if not sink_names:
        return current_sink
    try:
        current_index = sink_names.index(current_sink)
        next_index = (current_index + 1) % len(sink_names)
    except ValueError:
        next_index = 0
    return sink_names[next_index]


def get_default_sink_name() -> str:
    result = subprocess.run(
        ["pactl", "get-default-sink"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def set_default_sink(sink_name: str) -> None:
    subprocess.run(
        ["pactl", "set-default-sink", sink_name],
        capture_output=True,
    )


def move_all_playing_streams_to_sink(target_sink_name: str) -> None:
    sinks_output = subprocess.run(
        ["pactl", "list", "sinks", "short"],
        capture_output=True,
        text=True,
    )
    target_sink_index = None
    for line in sinks_output.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) >= 2 and fields[1] == target_sink_name:
            target_sink_index = fields[0]
            break

    if target_sink_index is None:
        return

    inputs_output = subprocess.run(
        ["pactl", "list", "sink-inputs", "short"],
        capture_output=True,
        text=True,
    )
    for line in inputs_output.stdout.splitlines():
        fields = line.split("\t")
        if fields:
            subprocess.run(
                ["pactl", "move-sink-input", fields[0], target_sink_index],
                capture_output=True,
            )


def get_sink_human_readable_description(sink_name: str) -> str:
    result = subprocess.run(
        ["pactl", "list", "sinks"],
        capture_output=True,
        text=True,
    )
    found_sink = False
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("Name:") and stripped.split(None, 1)[1] == sink_name:
            found_sink = True
        elif found_sink and stripped.startswith("Description:"):
            return stripped.split("Description: ", 1)[1]
    return sink_name


def send_sink_switch_notification(sink_name: str) -> None:
    description = get_sink_human_readable_description(sink_name)
    subprocess.run(
        [
            "notify-send",
            "-t",
            "3000",
            "-i",
            str(AUDIO_OUTPUT_ICONS_DIR / "volume-high.png"),
            "Audio Output",
            description,
        ],
        capture_output=True,
    )


def main() -> None:
    all_sinks = list_all_hardware_sink_names()
    current_default = get_default_sink_name()
    next_sink = find_next_sink_in_cycle(all_sinks, current_default)

    set_default_sink(next_sink)
    move_all_playing_streams_to_sink(next_sink)
    send_sink_switch_notification(next_sink)


if __name__ == "__main__":
    main()
