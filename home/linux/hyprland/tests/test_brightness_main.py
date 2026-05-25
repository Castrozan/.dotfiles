from unittest.mock import MagicMock, patch

import brightness


def make_brightnessctl_machine_output(percent: int) -> MagicMock:
    mock_result = MagicMock()
    mock_result.stdout = f"amdgpu_bl2,backlight,{percent * 1000},{percent}%,100000"
    return mock_result


class TestMain:
    def test_increment_uses_normal_step(self):
        with (
            patch("brightness.increase_brightness") as mock_increase,
            patch("brightness.sys.argv", ["cmd", "--inc"]),
        ):
            brightness.main()
            mock_increase.assert_called_once_with(brightness.BRIGHTNESS_STEP_NORMAL)

    def test_decrement_uses_normal_step(self):
        with (
            patch("brightness.decrease_brightness") as mock_decrease,
            patch("brightness.sys.argv", ["cmd", "--dec"]),
        ):
            brightness.main()
            mock_decrease.assert_called_once_with(brightness.BRIGHTNESS_STEP_NORMAL)

    def test_precise_increment_uses_precise_step(self):
        with (
            patch("brightness.increase_brightness") as mock_increase,
            patch("brightness.sys.argv", ["cmd", "--inc-precise"]),
        ):
            brightness.main()
            mock_increase.assert_called_once_with(brightness.BRIGHTNESS_STEP_PRECISE)

    def test_precise_decrement_uses_precise_step(self):
        with (
            patch("brightness.decrease_brightness") as mock_decrease,
            patch("brightness.sys.argv", ["cmd", "--dec-precise"]),
        ):
            brightness.main()
            mock_decrease.assert_called_once_with(brightness.BRIGHTNESS_STEP_PRECISE)

    def test_get_brightness_prints_hardware_value(self, capsys):
        with (
            patch(
                "brightness.subprocess.run",
                return_value=make_brightnessctl_machine_output(75),
            ),
            patch("brightness.sys.argv", ["cmd", "--get"]),
        ):
            brightness.main()

        assert capsys.readouterr().out.strip() == "75"

    def test_default_action_is_get(self, capsys):
        with (
            patch(
                "brightness.subprocess.run",
                return_value=make_brightnessctl_machine_output(50),
            ),
            patch("brightness.sys.argv", ["cmd"]),
        ):
            brightness.main()

        assert capsys.readouterr().out.strip() == "50"
