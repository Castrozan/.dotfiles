from unittest.mock import MagicMock, patch

import mouse_poll_rate


class TestShowDeviceInfo:
    def test_displays_device_information(self, capsys):
        mock_usb_path = MagicMock()

        call_counter = {"n": 0}
        ordered_values = ["ATK Mouse", "373b", "1234", "480", " 2.00 "]

        def read_sysfs_side_effect(path, default="unknown"):
            idx = call_counter["n"]
            call_counter["n"] += 1
            if idx < len(ordered_values):
                return ordered_values[idx]
            return default

        with patch(
            "atk_mouse_device.find_atk_usb_device_path",
            return_value=mock_usb_path,
        ):
            with patch(
                "atk_mouse_device.read_sysfs_attribute",
                side_effect=read_sysfs_side_effect,
            ):
                with patch(
                    "atk_mouse_device.find_atk_hidraw_config_interface",
                    return_value="/dev/hidraw0",
                ):
                    with patch(
                        "mouse_poll_rate.get_current_rate",
                        return_value="8000Hz",
                    ):
                        mouse_poll_rate.show_device_info()
                        output = capsys.readouterr().out
                        assert "ATK Mouse" in output
                        assert "480" in output
                        assert "8000Hz" in output


class TestMain:
    def test_get_subcommand(self):
        with patch("mouse_poll_rate.sys.argv", ["cmd", "get"]):
            with patch(
                "mouse_poll_rate.get_current_rate", return_value="4000Hz"
            ) as mock_get:
                mouse_poll_rate.main()
                mock_get.assert_called_once()

    def test_set_subcommand(self):
        with patch("mouse_poll_rate.sys.argv", ["cmd", "set", "8k"]):
            with patch("mouse_poll_rate.set_rate") as mock_set:
                mouse_poll_rate.main()
                mock_set.assert_called_once_with("8k")

    def test_info_subcommand(self):
        with patch("mouse_poll_rate.sys.argv", ["cmd", "info"]):
            with patch("mouse_poll_rate.show_device_info") as mock_info:
                mouse_poll_rate.main()
                mock_info.assert_called_once()

    def test_no_args_exits_with_usage(self):
        with patch("mouse_poll_rate.sys.argv", ["cmd"]):
            try:
                mouse_poll_rate.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1

    def test_set_without_rate_exits(self):
        with patch("mouse_poll_rate.sys.argv", ["cmd", "set"]):
            try:
                mouse_poll_rate.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1

    def test_unknown_subcommand_exits(self):
        with patch("mouse_poll_rate.sys.argv", ["cmd", "bogus"]):
            try:
                mouse_poll_rate.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1
