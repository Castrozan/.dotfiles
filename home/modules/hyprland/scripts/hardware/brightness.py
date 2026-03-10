import subprocess
import sys

BRIGHTNESS_STEP_NORMAL = 10
BRIGHTNESS_STEP_PRECISE = 1


def get_brightness_percentage() -> int:
    result = subprocess.run(["brightnessctl", "-m"], capture_output=True, text=True)
    fields = result.stdout.strip().split(",")
    return int(fields[3].replace("%", ""))


def change_brightness(adjustment: str) -> None:
    subprocess.run(
        ["brightnessctl", "set", adjustment],
        capture_output=True,
    )
    current_brightness = get_brightness_percentage()
    subprocess.run(["quickshell-osd-send", "brightness", str(current_brightness)])


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "--get"

    match action:
        case "--inc":
            change_brightness(f"+{BRIGHTNESS_STEP_NORMAL}%")
        case "--dec":
            change_brightness(f"{BRIGHTNESS_STEP_NORMAL}%-")
        case "--inc-precise":
            change_brightness(f"+{BRIGHTNESS_STEP_PRECISE}%")
        case "--dec-precise":
            change_brightness(f"{BRIGHTNESS_STEP_PRECISE}%-")
        case _:
            print(get_brightness_percentage())


if __name__ == "__main__":
    main()
