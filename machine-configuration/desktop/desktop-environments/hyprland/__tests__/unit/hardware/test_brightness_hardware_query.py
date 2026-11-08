from unittest.mock import patch

import brightness


class TestGetHardwareBrightnessPercentage:
    def test_parses_every_brightnessctl_machine_output_percentage(
        self, make_brightnessctl_machine_output
    ):
        misparsed = []
        for percentage in range(101):
            with patch(
                "brightness.subprocess.run",
                return_value=make_brightnessctl_machine_output(percentage),
            ):
                if brightness.get_hardware_brightness_percentage() != percentage:
                    misparsed.append(percentage)
        assert misparsed == []
