import importlib
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, call

import pytest


@pytest.fixture
def keyboard_modules(monkeypatch):
    directory = Path(__file__).resolve().parents[2] / "scripts" / "keyboard-backlight"
    monkeypatch.syspath_prepend(str(directory))
    usb = ModuleType("usb")
    usb.core = MagicMock()
    monkeypatch.setitem(sys.modules, "usb", usb)
    monkeypatch.setitem(sys.modules, "usb.core", usb.core)
    monkeypatch.setitem(sys.modules, "usb.util", ModuleType("usb.util"))
    names = (
        "alienware_led_controller",
        "set_keyboard_brightness",
        "set_keyboard_color",
        "reset_keyboard_backlight",
    )
    for name in names:
        monkeypatch.delitem(sys.modules, name, raising=False)
    return {name: importlib.import_module(name) for name in names}


def test_hid_transfer_uses_fixed_report_size_and_control_requests(keyboard_modules):
    controller = keyboard_modules["alienware_led_controller"]
    device = MagicMock()
    device.ctrl_transfer.side_effect = [None, bytes([9, 8, 7])]

    response = controller.send_hid_command(device, "263200020104")

    payload = bytearray.fromhex("03263200020104") + bytearray(26)
    assert device.ctrl_transfer.call_args_list == [
        call(0x21, 0x09, 0x0200, 0x00, payload),
        call(0xA1, 0x01, 0x0100, 0x00, 33),
    ]
    assert response == bytearray([9, 8, 7])


@pytest.mark.parametrize("driver_active", [False, True])
def test_acquisition_resets_and_conditionally_detaches_driver(
    keyboard_modules, driver_active
):
    controller = keyboard_modules["alienware_led_controller"]
    device = controller.usb.core.find.return_value
    device.is_kernel_driver_active.return_value = driver_active
    device[0].interfaces.return_value[0].bInterfaceNumber = 4

    assert controller.acquire_alienware_led_controller() is device

    controller.usb.core.find.assert_called_once_with(idVendor=0x187C, idProduct=0x0550)
    device.reset.assert_called_once_with()
    if driver_active:
        device.detach_kernel_driver.assert_called_once_with(4)
    else:
        device.detach_kernel_driver.assert_not_called()


def test_missing_controller_exits_before_usb_operations(keyboard_modules, capsys):
    controller = keyboard_modules["alienware_led_controller"]
    controller.usb.core.find.return_value = None

    with pytest.raises(SystemExit) as error:
        controller.acquire_alienware_led_controller()

    assert error.value.code == 1
    assert "187c:0550" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("module_name", "arguments", "color_command", "dimming_command"),
    [
        ("set_keyboard_brightness", ["5"], "2400ffff000100ffff", "265f0010"),
        ("set_keyboard_brightness", ["0"], "2400ffff000100ffff", "26640010"),
        ("set_keyboard_brightness", ["100"], "2400ffff000100ffff", "26000010"),
        ("set_keyboard_color", ["255", "0", "128"], "2400ffff0001ff0080", None),
        ("reset_keyboard_backlight", [], "2400ffff000100ffff", "26000010"),
    ],
)
def test_commands_preserve_animation_sequence_and_reset(
    keyboard_modules,
    monkeypatch,
    module_name,
    arguments,
    color_command,
    dimming_command,
):
    controller = keyboard_modules["alienware_led_controller"]
    operations = MagicMock()
    device = operations.device
    monkeypatch.setattr(
        controller, "cycle_alienware_wmi_kernel_driver", operations.cycle
    )
    monkeypatch.setattr(
        controller, "acquire_alienware_led_controller", operations.acquire
    )
    operations.acquire.return_value = device
    monkeypatch.setattr(controller, "send_hid_command", operations.send)
    monkeypatch.setattr(sys, "argv", ["keyboard-command", *arguments])

    keyboard_modules[module_name].main()

    zones = "000102030405060708090a0b0c0d0e0f"
    commands = [
        "2200040000005d",
        "2200010000005d",
        "23010010" + zones,
        color_command,
        "2200030000005d",
        "2200060000005d",
    ]
    if dimming_command is not None:
        commands.append(dimming_command + zones)
    assert operations.mock_calls == [
        call.cycle(),
        call.acquire(),
        *(call.send(device, command) for command in commands),
        call.device.reset(),
    ]


@pytest.mark.parametrize(
    ("module_name", "arguments", "error_type"),
    [
        ("set_keyboard_brightness", [], SystemExit),
        ("set_keyboard_brightness", ["-1"], SystemExit),
        ("set_keyboard_brightness", ["101"], SystemExit),
        ("set_keyboard_brightness", ["invalid"], ValueError),
        ("set_keyboard_color", ["1", "2"], SystemExit),
        ("set_keyboard_color", ["256", "0", "0"], SystemExit),
        ("set_keyboard_color", ["0", "-1", "0"], SystemExit),
        ("set_keyboard_color", ["0", "0", "256"], SystemExit),
    ],
)
def test_invalid_arguments_never_touch_hardware(
    keyboard_modules, monkeypatch, module_name, arguments, error_type
):
    controller = keyboard_modules["alienware_led_controller"]
    cycle = MagicMock()
    monkeypatch.setattr(controller, "cycle_alienware_wmi_kernel_driver", cycle)
    monkeypatch.setattr(sys, "argv", ["keyboard-command", *arguments])

    with pytest.raises(error_type):
        keyboard_modules[module_name].main()

    cycle.assert_not_called()
    controller.usb.core.find.assert_not_called()
