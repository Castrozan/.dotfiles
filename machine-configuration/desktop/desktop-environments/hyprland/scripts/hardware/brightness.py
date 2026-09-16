import os
import subprocess
import sys
from pathlib import Path

BRIGHTNESS_STEP_NORMAL = 10
BRIGHTNESS_STEP_PRECISE = 1
HARDWARE_BRIGHTNESS_MINIMUM_PERCENT = 1
HARDWARE_BRIGHTNESS_MAXIMUM_PERCENT = 100
GAMMA_MINIMUM_PERCENT = 10
GAMMA_MAXIMUM_PERCENT = 100
GAMMA_STATE_PATH = (
    Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state")))
    / "hypr"
    / "gamma"
)


def get_hardware_brightness_percentage() -> int:
    result = subprocess.run(["brightnessctl", "-m"], capture_output=True, text=True)
    fields = result.stdout.strip().split(",")
    return int(fields[3].replace("%", ""))


def set_hardware_brightness_percentage(target_percent: int) -> None:
    subprocess.run(
        ["brightnessctl", "set", f"{target_percent}%"],
        capture_output=True,
    )


def read_persisted_gamma_percentage() -> int:
    try:
        return int(GAMMA_STATE_PATH.read_text().strip())
    except (FileNotFoundError, ValueError):
        return GAMMA_MAXIMUM_PERCENT


def write_persisted_gamma_percentage(value: int) -> None:
    GAMMA_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GAMMA_STATE_PATH.write_text(str(value))


def apply_compositor_gamma_percentage(value: int) -> bool:
    result = subprocess.run(
        ["hyprctl", "hyprsunset", "gamma", str(value)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def send_brightness_osd(value: int) -> None:
    subprocess.run(["quickshell-osd-send", "brightness", str(value)])


def increase_brightness(step: int) -> None:
    current_gamma = read_persisted_gamma_percentage()
    if current_gamma < GAMMA_MAXIMUM_PERCENT:
        next_gamma = min(GAMMA_MAXIMUM_PERCENT, current_gamma + step)
        if apply_compositor_gamma_percentage(next_gamma):
            write_persisted_gamma_percentage(next_gamma)
            send_brightness_osd(next_gamma)
            return
    current_hardware = get_hardware_brightness_percentage()
    next_hardware = min(HARDWARE_BRIGHTNESS_MAXIMUM_PERCENT, current_hardware + step)
    set_hardware_brightness_percentage(next_hardware)
    send_brightness_osd(next_hardware)


def decrease_brightness(step: int) -> None:
    current_hardware = get_hardware_brightness_percentage()
    if current_hardware > HARDWARE_BRIGHTNESS_MINIMUM_PERCENT:
        next_hardware = max(
            HARDWARE_BRIGHTNESS_MINIMUM_PERCENT, current_hardware - step
        )
        set_hardware_brightness_percentage(next_hardware)
        send_brightness_osd(next_hardware)
        return
    current_gamma = read_persisted_gamma_percentage()
    next_gamma = max(GAMMA_MINIMUM_PERCENT, current_gamma - step)
    if apply_compositor_gamma_percentage(next_gamma):
        write_persisted_gamma_percentage(next_gamma)
        send_brightness_osd(next_gamma)
    else:
        send_brightness_osd(current_hardware)


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "--get"

    match action:
        case "--inc":
            increase_brightness(BRIGHTNESS_STEP_NORMAL)
        case "--dec":
            decrease_brightness(BRIGHTNESS_STEP_NORMAL)
        case "--inc-precise":
            increase_brightness(BRIGHTNESS_STEP_PRECISE)
        case "--dec-precise":
            decrease_brightness(BRIGHTNESS_STEP_PRECISE)
        case _:
            print(get_hardware_brightness_percentage())


if __name__ == "__main__":
    main()
