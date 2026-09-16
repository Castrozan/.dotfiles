from unittest.mock import MagicMock, call, patch

import volume


class TestFindActiveSinkNameOrDefault:
    def test_returns_default_sink_when_running(self):
        default_result = MagicMock(stdout="alsa_output.pci\n")
        sinks_result = MagicMock(
            stdout="0\talsa_output.pci\tmodule\ts32le\t2ch\t48000Hz\tRUNNING\n"
        )

        with patch(
            "volume.subprocess.run",
            side_effect=[default_result, sinks_result],
        ):
            assert volume.find_active_sink_name_or_default() == "alsa_output.pci"

    def test_returns_running_hardware_sink_when_default_idle(self):
        default_result = MagicMock(stdout="alsa_output.pci\n")
        sinks_result = MagicMock(
            stdout=(
                "0\talsa_output.pci\tmodule\ts32le\t2ch\t48000Hz\tIDLE\n"
                "1\tbluez_output.bt\tmodule\ts16le\t2ch\t44100Hz\tRUNNING\n"
            )
        )

        with patch(
            "volume.subprocess.run",
            side_effect=[default_result, sinks_result],
        ):
            assert volume.find_active_sink_name_or_default() == "bluez_output.bt"

    def test_returns_default_sink_marker_when_none_running(self):
        default_result = MagicMock(stdout="alsa_output.pci\n")
        sinks_result = MagicMock(
            stdout="0\talsa_output.pci\tmodule\ts32le\t2ch\t48000Hz\tIDLE\n"
        )

        with patch(
            "volume.subprocess.run",
            side_effect=[default_result, sinks_result],
        ):
            assert volume.find_active_sink_name_or_default() == "@DEFAULT_SINK@"


class TestGetVolumeForActiveSink:
    def test_parses_volume_percentage(self):
        with patch(
            "volume.find_active_sink_name_or_default",
            return_value="alsa_output.pci",
        ):
            mock_result = MagicMock(
                stdout="Volume: front-left: 42000 /  65% / -11.22 dB"
            )
            with patch("volume.subprocess.run", return_value=mock_result):
                assert volume.get_volume_for_active_sink() == 65

    def test_returns_zero_when_no_match(self):
        with patch(
            "volume.find_active_sink_name_or_default",
            return_value="alsa_output.pci",
        ):
            mock_result = MagicMock(stdout="")
            with patch("volume.subprocess.run", return_value=mock_result):
                assert volume.get_volume_for_active_sink() == 0


class TestIsSinkMuted:
    def test_returns_true_when_muted(self):
        with patch(
            "volume.find_active_sink_name_or_default",
            return_value="alsa_output.pci",
        ):
            mock_result = MagicMock(stdout="Mute: yes\n")
            with patch("volume.subprocess.run", return_value=mock_result):
                assert volume.is_sink_muted() is True

    def test_returns_false_when_not_muted(self):
        with patch(
            "volume.find_active_sink_name_or_default",
            return_value="alsa_output.pci",
        ):
            mock_result = MagicMock(stdout="Mute: no\n")
            with patch("volume.subprocess.run", return_value=mock_result):
                assert volume.is_sink_muted() is False


class TestGetVolumeIconPath:
    def test_returns_mute_icon_when_muted(self):
        with patch("volume.get_volume_for_active_sink", return_value=50):
            with patch("volume.is_sink_muted", return_value=True):
                assert "volume-mute.png" in volume.get_volume_icon_path()

    def test_returns_mute_icon_when_volume_zero(self):
        with patch("volume.get_volume_for_active_sink", return_value=0):
            with patch("volume.is_sink_muted", return_value=False):
                assert "volume-mute.png" in volume.get_volume_icon_path()

    def test_returns_low_icon(self):
        with patch("volume.get_volume_for_active_sink", return_value=20):
            with patch("volume.is_sink_muted", return_value=False):
                assert "volume-low.png" in volume.get_volume_icon_path()

    def test_returns_mid_icon(self):
        with patch("volume.get_volume_for_active_sink", return_value=50):
            with patch("volume.is_sink_muted", return_value=False):
                assert "volume-mid.png" in volume.get_volume_icon_path()

    def test_returns_high_icon(self):
        with patch("volume.get_volume_for_active_sink", return_value=80):
            with patch("volume.is_sink_muted", return_value=False):
                assert "volume-high.png" in volume.get_volume_icon_path()


class TestIncreaseVolume:
    def test_sets_volume_and_sends_osd(self):
        with patch(
            "volume.find_active_sink_name_or_default",
            return_value="alsa_output.pci",
        ):
            with patch("volume.subprocess.run") as mock_run:
                with patch("volume.send_volume_osd"):
                    volume.increase_volume(5)

                    mock_run.assert_called_once_with(
                        ["pactl", "set-sink-volume", "alsa_output.pci", "+5%"],
                        capture_output=True,
                    )


class TestDecreaseVolume:
    def test_sets_volume_and_sends_osd(self):
        with patch(
            "volume.find_active_sink_name_or_default",
            return_value="alsa_output.pci",
        ):
            with patch("volume.subprocess.run") as mock_run:
                with patch("volume.send_volume_osd"):
                    volume.decrease_volume(5)

                    mock_run.assert_called_once_with(
                        ["pactl", "set-sink-volume", "alsa_output.pci", "-5%"],
                        capture_output=True,
                    )


class TestToggleMute:
    def test_sends_mute_osd_when_muted_after_toggle(self):
        with patch(
            "volume.find_active_sink_name_or_default",
            return_value="alsa_output.pci",
        ):
            with patch("volume.subprocess.run") as mock_run:
                with patch("volume.is_sink_muted", return_value=True):
                    volume.toggle_mute()

                    assert mock_run.call_count == 2
                    assert mock_run.call_args_list[0] == call(
                        ["pactl", "set-sink-mute", "alsa_output.pci", "toggle"],
                        capture_output=True,
                    )
                    assert mock_run.call_args_list[1] == call(
                        ["quickshell-osd-send", "mute", "true"]
                    )

    def test_sends_volume_osd_when_unmuted_after_toggle(self):
        with patch(
            "volume.find_active_sink_name_or_default",
            return_value="alsa_output.pci",
        ):
            with patch("volume.subprocess.run"):
                with patch("volume.is_sink_muted", return_value=False):
                    with patch("volume.send_volume_osd") as mock_osd:
                        volume.toggle_mute()
                        mock_osd.assert_called_once()
