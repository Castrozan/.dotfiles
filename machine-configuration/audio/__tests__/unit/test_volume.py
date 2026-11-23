from pathlib import Path
from unittest.mock import MagicMock, patch

import volume

VOLUME_ICON_BANDS = (
    (0, "volume-mute.png"),
    (30, "volume-low.png"),
    (60, "volume-mid.png"),
    (150, "volume-high.png"),
)


def icon_name_at(volume_percent: int, muted: bool = False) -> str:
    with patch("volume.get_volume_for_active_sink", return_value=volume_percent):
        with patch("volume.is_sink_muted", return_value=muted):
            return Path(volume.get_volume_icon_path()).name


def expected_icon_name(volume_percent: int, muted: bool) -> str:
    if muted:
        return "volume-mute.png"
    return next(
        icon for ceiling, icon in VOLUME_ICON_BANDS if volume_percent <= ceiling
    )


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
    def test_returns_the_expected_icon_for_every_volume_and_mute_state(self):
        mismatches = [
            (volume_percent, muted)
            for volume_percent in range(151)
            for muted in (False, True)
            if icon_name_at(volume_percent, muted)
            != expected_icon_name(volume_percent, muted)
        ]
        assert mismatches == []


class TestIncreaseVolume:
    def test_sets_volume(self):
        with patch(
            "volume.find_active_sink_name_or_default",
            return_value="alsa_output.pci",
        ):
            with patch("volume.subprocess.run") as mock_run:
                volume.increase_volume(5)

                mock_run.assert_called_once_with(
                    ["pactl", "set-sink-volume", "alsa_output.pci", "+5%"],
                    capture_output=True,
                )


class TestDecreaseVolume:
    def test_sets_volume(self):
        with patch(
            "volume.find_active_sink_name_or_default",
            return_value="alsa_output.pci",
        ):
            with patch("volume.subprocess.run") as mock_run:
                volume.decrease_volume(5)

                mock_run.assert_called_once_with(
                    ["pactl", "set-sink-volume", "alsa_output.pci", "-5%"],
                    capture_output=True,
                )


class TestToggleMute:
    def test_toggles_the_active_sink_mute(self):
        with patch(
            "volume.find_active_sink_name_or_default",
            return_value="alsa_output.pci",
        ):
            with patch("volume.subprocess.run") as mock_run:
                volume.toggle_mute()

                mock_run.assert_called_once_with(
                    ["pactl", "set-sink-mute", "alsa_output.pci", "toggle"],
                    capture_output=True,
                )
