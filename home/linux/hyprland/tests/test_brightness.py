from unittest.mock import MagicMock, call, patch

import brightness


class TestGetBrightnessPercentage:
    def test_parses_brightnessctl_machine_output(self):
        mock_result = MagicMock()
        mock_result.stdout = "intel_backlight,backlight,45000,45%,100000"

        with patch("brightness.subprocess.run", return_value=mock_result):
            assert brightness.get_brightness_percentage() == 45

    def test_parses_single_digit_brightness(self):
        mock_result = MagicMock()
        mock_result.stdout = "intel_backlight,backlight,5000,5%,100000"

        with patch("brightness.subprocess.run", return_value=mock_result):
            assert brightness.get_brightness_percentage() == 5

    def test_parses_full_brightness(self):
        mock_result = MagicMock()
        mock_result.stdout = "intel_backlight,backlight,100000,100%,100000"

        with patch("brightness.subprocess.run", return_value=mock_result):
            assert brightness.get_brightness_percentage() == 100


class TestChangeBrightness:
    def test_sets_brightness_and_sends_osd(self):
        brightnessctl_result = MagicMock()
        brightnessctl_get_result = MagicMock()
        brightnessctl_get_result.stdout = "intel_backlight,backlight,60000,60%,100000"

        def run_side_effect(args, **kwargs):
            if args == ["brightnessctl", "-m"]:
                return brightnessctl_get_result
            return brightnessctl_result

        with patch(
            "brightness.subprocess.run", side_effect=run_side_effect
        ) as mock_run:
            brightness.change_brightness("+10%")

            assert mock_run.call_args_list[0] == call(
                ["brightnessctl", "set", "+10%"], capture_output=True
            )
            assert mock_run.call_args_list[2] == call(
                ["quickshell-osd-send", "brightness", "60"]
            )


class TestMain:
    def test_increment_brightness(self):
        with patch("brightness.change_brightness") as mock_change:
            with patch("brightness.sys.argv", ["cmd", "--inc"]):
                brightness.main()
                mock_change.assert_called_once_with("+10%")

    def test_decrement_brightness(self):
        with patch("brightness.change_brightness") as mock_change:
            with patch("brightness.sys.argv", ["cmd", "--dec"]):
                brightness.main()
                mock_change.assert_called_once_with("10%-")

    def test_precise_increment(self):
        with patch("brightness.change_brightness") as mock_change:
            with patch("brightness.sys.argv", ["cmd", "--inc-precise"]):
                brightness.main()
                mock_change.assert_called_once_with("+1%")

    def test_precise_decrement(self):
        with patch("brightness.change_brightness") as mock_change:
            with patch("brightness.sys.argv", ["cmd", "--dec-precise"]):
                brightness.main()
                mock_change.assert_called_once_with("1%-")

    def test_get_brightness_prints_value(self, capsys):
        mock_result = MagicMock()
        mock_result.stdout = "intel_backlight,backlight,75000,75%,100000"

        with patch("brightness.subprocess.run", return_value=mock_result):
            with patch("brightness.sys.argv", ["cmd", "--get"]):
                brightness.main()

        assert capsys.readouterr().out.strip() == "75"

    def test_default_action_is_get(self, capsys):
        mock_result = MagicMock()
        mock_result.stdout = "intel_backlight,backlight,50000,50%,100000"

        with patch("brightness.subprocess.run", return_value=mock_result):
            with patch("brightness.sys.argv", ["cmd"]):
                brightness.main()

        assert capsys.readouterr().out.strip() == "50"
