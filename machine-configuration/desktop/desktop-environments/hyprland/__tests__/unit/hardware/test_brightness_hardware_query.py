from unittest.mock import patch

import brightness


class TestGetHardwareBrightnessPercentage:
    def test_parses_brightnessctl_machine_output(
        self, make_brightnessctl_machine_output
    ):
        with patch(
            "brightness.subprocess.run",
            return_value=make_brightnessctl_machine_output(45),
        ):
            assert brightness.get_hardware_brightness_percentage() == 45

    def test_parses_single_digit_brightness(self, make_brightnessctl_machine_output):
        with patch(
            "brightness.subprocess.run",
            return_value=make_brightnessctl_machine_output(5),
        ):
            assert brightness.get_hardware_brightness_percentage() == 5

    def test_parses_full_brightness(self, make_brightnessctl_machine_output):
        with patch(
            "brightness.subprocess.run",
            return_value=make_brightnessctl_machine_output(100),
        ):
            assert brightness.get_hardware_brightness_percentage() == 100
