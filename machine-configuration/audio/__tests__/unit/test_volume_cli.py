from unittest.mock import patch

import volume


class TestMain:
    def test_get_volume_by_default(self, capsys):
        with patch("volume.sys.argv", ["cmd"]):
            with patch("volume.get_volume_for_active_sink", return_value=65):
                volume.main()
                assert capsys.readouterr().out.strip() == "65"

    def test_get_volume_with_flag(self, capsys):
        with patch("volume.sys.argv", ["cmd", "--get"]):
            with patch("volume.get_volume_for_active_sink", return_value=50):
                volume.main()
                assert capsys.readouterr().out.strip() == "50"

    def test_increase_volume(self):
        with patch("volume.sys.argv", ["cmd", "--inc"]):
            with patch("volume.increase_volume") as mock_inc:
                volume.main()
                mock_inc.assert_called_once_with(5)

    def test_decrease_volume(self):
        with patch("volume.sys.argv", ["cmd", "--dec"]):
            with patch("volume.decrease_volume") as mock_dec:
                volume.main()
                mock_dec.assert_called_once_with(5)

    def test_precise_increase(self):
        with patch("volume.sys.argv", ["cmd", "--inc-precise"]):
            with patch("volume.increase_volume") as mock_inc:
                volume.main()
                mock_inc.assert_called_once_with(1)

    def test_precise_decrease(self):
        with patch("volume.sys.argv", ["cmd", "--dec-precise"]):
            with patch("volume.decrease_volume") as mock_dec:
                volume.main()
                mock_dec.assert_called_once_with(1)

    def test_toggle_mute(self):
        with patch("volume.sys.argv", ["cmd", "--toggle"]):
            with patch("volume.toggle_mute") as mock_toggle:
                volume.main()
                mock_toggle.assert_called_once()

    def test_toggle_mic(self):
        with patch("volume.sys.argv", ["cmd", "--toggle-mic"]):
            with patch("volume.toggle_microphone_mute") as mock_toggle:
                volume.main()
                mock_toggle.assert_called_once()

    def test_get_icon(self, capsys):
        with patch("volume.sys.argv", ["cmd", "--get-icon"]):
            with patch(
                "volume.get_volume_icon_path",
                return_value="/path/volume-high.png",
            ):
                volume.main()
                assert "volume-high.png" in capsys.readouterr().out

    def test_get_mic_icon(self, capsys):
        with patch("volume.sys.argv", ["cmd", "--get-mic-icon"]):
            volume.main()
            assert "microphone.png" in capsys.readouterr().out
