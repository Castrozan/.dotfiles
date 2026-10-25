import json
import math
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
        check=True,
    )


def read_persisted_gamma_percentage() -> int:
    try:
        return int(GAMMA_STATE_PATH.read_text().strip())
    except (FileNotFoundError, ValueError):
        return GAMMA_MAXIMUM_PERCENT


def write_persisted_gamma_percentage(value: int) -> None:
    GAMMA_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GAMMA_STATE_PATH.write_text(str(value))


def get_gamma_percentage() -> int:
    result = subprocess.run(
        ["hyprctl", "hyprsunset", "gamma"], capture_output=True, text=True
    )
    try:
        if result.returncode == 0:
            return round(float(result.stdout.strip()))
    except ValueError:
        pass
    return read_persisted_gamma_percentage()


def uses_hardware_brightness() -> bool:
    result = subprocess.run(
        ["hyprctl", "-j", "monitors"], capture_output=True, text=True
    )
    try:
        monitors = json.loads(result.stdout) if result.returncode == 0 else []
        if monitors:
            return any(
                monitor["name"].startswith(("eDP-", "LVDS-", "DSI-"))
                for monitor in monitors
            )
    except (ValueError, KeyError, TypeError):
        pass
    return True


def apply_compositor_gamma_percentage(value: int) -> bool:
    result = subprocess.run(
        ["hyprctl", "hyprsunset", "gamma", str(value)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def combined_percentage(hardware: int, gamma: int, hardware_active: bool) -> float:
    if not hardware_active:
        return gamma
    return round(max(HARDWARE_BRIGHTNESS_MINIMUM_PERCENT, hardware) * gamma / 100, 2)


def get_brightness_state() -> dict:
    hardware = get_hardware_brightness_percentage()
    gamma = get_gamma_percentage()
    hardware_active = uses_hardware_brightness()
    return {
        "value": combined_percentage(hardware, gamma, hardware_active),
        "minimum": 0.1 if hardware_active else GAMMA_MINIMUM_PERCENT,
        "hardware": hardware,
        "gamma": gamma,
        "hardwareActive": hardware_active,
    }


def send_brightness_osd(value: float) -> None:
    subprocess.run(["quickshell-osd-send", "brightness", str(value)])


def brightness_targets(target: float, state: dict) -> tuple[int, int]:
    if not math.isfinite(target):
        raise ValueError("Brightness must be finite")
    target = max(state["minimum"], min(100, target))
    if not state["hardwareActive"]:
        return state["hardware"], round(target)
    hardware = max(1, round(target))
    gamma = 100
    if target < 1:
        gamma = round(target * 100)
    return hardware, gamma


def set_brightness_percentage(target: float) -> None:
    state = get_brightness_state()
    hardware, gamma = brightness_targets(target, state)
    if gamma != state["gamma"]:
        if not apply_compositor_gamma_percentage(gamma):
            send_brightness_osd(state["value"])
            raise RuntimeError("Could not apply compositor dimming")
    write_persisted_gamma_percentage(gamma)
    if state["hardwareActive"] and hardware != state["hardware"]:
        set_hardware_brightness_percentage(hardware)
    send_brightness_osd(get_brightness_state()["value"])


def increase_brightness(step: int) -> None:
    state = get_brightness_state()
    if state["gamma"] < GAMMA_MAXIMUM_PERCENT or not state["hardwareActive"]:
        gamma = min(GAMMA_MAXIMUM_PERCENT, state["gamma"] + step)
        if apply_compositor_gamma_percentage(gamma):
            write_persisted_gamma_percentage(gamma)
            send_brightness_osd(
                combined_percentage(state["hardware"], gamma, state["hardwareActive"])
            )
            return
        if not state["hardwareActive"]:
            send_brightness_osd(state["value"])
            return
    hardware = min(100, state["hardware"] + step)
    set_hardware_brightness_percentage(hardware)
    send_brightness_osd(combined_percentage(hardware, state["gamma"], True))


def decrease_brightness(step: int) -> None:
    state = get_brightness_state()
    if state["hardwareActive"] and state["hardware"] > 1:
        hardware = max(1, state["hardware"] - step)
        set_hardware_brightness_percentage(hardware)
        send_brightness_osd(combined_percentage(hardware, state["gamma"], True))
        return
    gamma = max(GAMMA_MINIMUM_PERCENT, state["gamma"] - step)
    if apply_compositor_gamma_percentage(gamma):
        write_persisted_gamma_percentage(gamma)
        send_brightness_osd(
            combined_percentage(state["hardware"], gamma, state["hardwareActive"])
        )
    else:
        send_brightness_osd(state["value"])


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "--get"
    actions = {
        "--inc": lambda: increase_brightness(BRIGHTNESS_STEP_NORMAL),
        "--dec": lambda: decrease_brightness(BRIGHTNESS_STEP_NORMAL),
        "--inc-precise": lambda: increase_brightness(BRIGHTNESS_STEP_PRECISE),
        "--dec-precise": lambda: decrease_brightness(BRIGHTNESS_STEP_PRECISE),
        "--set": lambda: set_brightness_percentage(float(sys.argv[2])),
        "--get-state": lambda: print(json.dumps(get_brightness_state())),
    }
    handler = actions.get(action)
    if handler is not None:
        handler()
    else:
        print(f"{get_brightness_state()['value']:g}")


if __name__ == "__main__":
    main()
