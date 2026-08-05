from unittest.mock import MagicMock, patch

import brightness


def make_brightnessctl_machine_output(percent: int) -> MagicMock:
    mock_result = MagicMock()
    mock_result.stdout = f"amdgpu_bl2,backlight,{percent * 1000},{percent}%,100000"
    return mock_result


class TestGetHardwareBrightnessPercentage:
    def test_parses_brightnessctl_machine_output(self):
        with patch(
            "brightness.subprocess.run",
            return_value=make_brightnessctl_machine_output(45),
        ):
            assert brightness.get_hardware_brightness_percentage() == 45

    def test_parses_single_digit_brightness(self):
        with patch(
            "brightness.subprocess.run",
            return_value=make_brightnessctl_machine_output(5),
        ):
            assert brightness.get_hardware_brightness_percentage() == 5

    def test_parses_full_brightness(self):
        with patch(
            "brightness.subprocess.run",
            return_value=make_brightnessctl_machine_output(100),
        ):
            assert brightness.get_hardware_brightness_percentage() == 100
