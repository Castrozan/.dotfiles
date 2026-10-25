import json
from types import SimpleNamespace

import brightness
import pytest


@pytest.fixture
def runtime(monkeypatch, tmp_path):
    state = {
        "hardware": 50,
        "gamma": 100,
        "monitors": [{"name": "eDP-1"}],
        "gamma_failure": False,
        "osd": [],
        "hardware_writes": [],
    }
    monkeypatch.setattr(brightness, "GAMMA_STATE_PATH", tmp_path / "gamma")

    def run(command, **kwargs):
        result = SimpleNamespace(returncode=0, stdout="")
        if command == ["brightnessctl", "-m"]:
            result.stdout = f"test,backlight,1,{state['hardware']}%,255"
        elif command[:2] == ["brightnessctl", "set"]:
            state["hardware"] = int(command[2].removesuffix("%"))
            state["hardware_writes"].append(state["hardware"])
        elif command == ["hyprctl", "-j", "monitors"]:
            result.stdout = json.dumps(state["monitors"])
        elif command == ["hyprctl", "hyprsunset", "gamma"]:
            result.stdout = str(state["gamma"])
        elif command[:3] == ["hyprctl", "hyprsunset", "gamma"]:
            if state["gamma_failure"]:
                result.returncode = 1
            else:
                state["gamma"] = int(command[3])
        elif command[:2] == ["quickshell-osd-send", "brightness"]:
            state["osd"].append(float(command[2]))
        else:
            pytest.fail(f"Unexpected external command: {command}")
        return result

    monkeypatch.setattr(brightness.subprocess, "run", run)
    return state


def test_reads_live_gamma_instead_of_stale_saved_value(runtime):
    runtime["gamma"] = 40
    brightness.GAMMA_STATE_PATH.write_text("100")
    assert brightness.get_brightness_state() == {
        "value": 20,
        "minimum": 0.1,
        "hardware": 50,
        "gamma": 40,
        "hardwareActive": True,
    }


@pytest.mark.parametrize(
    ("target", "hardware", "gamma", "effective"),
    [(50, 50, 100, 50), (0.5, 1, 50, 0.5), (0, 1, 10, 0.1), (100, 100, 100, 100)],
)
def test_absolute_control_composes_hardware_and_gamma(
    runtime, target, hardware, gamma, effective
):
    brightness.set_brightness_percentage(target)
    assert runtime["hardware"] == hardware
    assert runtime["gamma"] == gamma
    assert brightness.get_brightness_state()["value"] == effective
    assert runtime["osd"][-1] == effective


def test_raising_absolute_level_clears_old_software_dimming(runtime):
    runtime.update(hardware=1, gamma=30)
    brightness.set_brightness_percentage(40)
    assert (runtime["hardware"], runtime["gamma"]) == (40, 100)
    assert runtime["osd"] == [40]


def test_key_steps_cross_hardware_floor_without_inverting_reported_level(runtime):
    runtime["hardware"] = 2
    brightness.decrease_brightness(1)
    brightness.decrease_brightness(1)
    brightness.increase_brightness(1)
    brightness.increase_brightness(1)
    assert runtime["osd"] == [1, 0.99, 1, 2]
    assert (runtime["hardware"], runtime["gamma"]) == (2, 100)


def test_external_only_control_changes_gamma_and_preserves_disabled_backlight(runtime):
    runtime.update(hardware=0, monitors=[{"name": "DP-1"}])
    assert brightness.get_brightness_state()["value"] == 100
    assert brightness.get_brightness_state()["minimum"] == 10
    brightness.set_brightness_percentage(40)
    brightness.decrease_brightness(10)
    brightness.increase_brightness(1)
    assert runtime["gamma"] == 31
    assert runtime["osd"] == [40, 30, 31]
    assert runtime["hardware_writes"] == []
    assert runtime["hardware"] == 0


def test_failed_external_dimming_does_not_claim_success_or_change_backlight(runtime):
    runtime.update(hardware=0, gamma_failure=True, monitors=[{"name": "DP-1"}])
    with pytest.raises(RuntimeError, match="compositor dimming"):
        brightness.set_brightness_percentage(30)
    assert runtime["osd"] == [100]
    assert runtime["hardware_writes"] == []
    assert not brightness.GAMMA_STATE_PATH.exists()


@pytest.mark.parametrize("target", [float("nan"), float("inf")])
def test_rejects_non_finite_levels_before_writing(runtime, target):
    with pytest.raises(ValueError, match="finite"):
        brightness.set_brightness_percentage(target)
    assert runtime["hardware_writes"] == []
    assert runtime["osd"] == []


def test_main_exposes_combined_json_state(runtime, monkeypatch, capsys):
    runtime.update(hardware=1, gamma=40)
    monkeypatch.setattr(brightness.sys, "argv", ["brightness", "--get-state"])
    brightness.main()
    assert json.loads(capsys.readouterr().out)["value"] == 0.4
    monkeypatch.setattr(brightness.sys, "argv", ["brightness", "--get"])
    brightness.main()
    assert capsys.readouterr().out.strip() == "0.4"
