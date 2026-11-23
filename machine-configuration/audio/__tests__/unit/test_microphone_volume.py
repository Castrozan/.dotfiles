from unittest.mock import patch

import volume


class TestMicrophoneVolume:
    def test_increase_microphone_volume(self):
        with patch("volume.subprocess.run") as mock_run:
            volume.increase_microphone_volume(5)

            mock_run.assert_called_once_with(
                ["pactl", "set-source-volume", "@DEFAULT_SOURCE@", "+5%"],
                capture_output=True,
            )

    def test_decrease_microphone_volume(self):
        with patch("volume.subprocess.run") as mock_run:
            volume.decrease_microphone_volume(5)

            mock_run.assert_called_once_with(
                ["pactl", "set-source-volume", "@DEFAULT_SOURCE@", "-5%"],
                capture_output=True,
            )


class TestToggleMicrophoneMute:
    def test_toggles_the_default_source_mute(self):
        with patch("volume.subprocess.run") as mock_run:
            volume.toggle_microphone_mute()

            mock_run.assert_called_once_with(
                ["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"],
                capture_output=True,
            )
