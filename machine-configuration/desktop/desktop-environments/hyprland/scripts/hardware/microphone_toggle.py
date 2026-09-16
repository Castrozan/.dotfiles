import subprocess
import sys

MIC_SOURCE_NAME = "@DEFAULT_SOURCE@"


def get_microphone_mute_status() -> str:
    result = subprocess.run(
        ["pactl", "get-source-mute", MIC_SOURCE_NAME],
        capture_output=True,
        text=True,
    )
    return "muted" if "yes" in result.stdout else "unmuted"


def get_microphone_volume() -> str:
    result = subprocess.run(
        ["pactl", "get-source-volume", MIC_SOURCE_NAME],
        capture_output=True,
        text=True,
    )
    first_line = result.stdout.strip().split("\n")[0]
    for field in first_line.split():
        if field.endswith("%"):
            return field.replace("%", "")
    return "0"


def output_microphone_status_json() -> None:
    status = get_microphone_mute_status()
    volume = get_microphone_volume()

    if status == "muted":
        print('{"text":"󰖁","tooltip":"Microphone MUTED","class":"muted"}')
    else:
        print(
            '{"text":"󰍰",'
            f'"tooltip":"Microphone unmuted ({volume}%)",'
            '"class":"unmuted"}'
        )


def toggle_microphone_mute() -> None:
    subprocess.run(
        ["pactl", "set-source-mute", MIC_SOURCE_NAME, "toggle"],
        capture_output=True,
    )


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    match action:
        case "status":
            output_microphone_status_json()
        case "toggle":
            toggle_microphone_mute()
        case _:
            print(
                "Usage: hypr-microphone-toggle {status|toggle}",
                file=sys.stderr,
            )
            raise SystemExit(1)


if __name__ == "__main__":
    main()
