from unittest.mock import patch

import brightness


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

    def test_get_brightness_prints_hardware_value(
        self, capsys, make_brightnessctl_machine_output
    ):
        with (
            patch(
                "brightness.subprocess.run",
                return_value=make_brightnessctl_machine_output(75),
            ),
            patch("brightness.sys.argv", ["cmd", "--get"]),
        ):
            brightness.main()

        assert capsys.readouterr().out.strip() == "75"

    def test_default_action_is_get(self, capsys, make_brightnessctl_machine_output):
        with (
            patch(
                "brightness.subprocess.run",
                return_value=make_brightnessctl_machine_output(50),
            ),
            patch("brightness.sys.argv", ["cmd"]),
        ):
            brightness.main()

        assert capsys.readouterr().out.strip() == "50"
