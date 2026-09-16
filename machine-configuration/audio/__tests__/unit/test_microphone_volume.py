from unittest.mock import MagicMock, call, patch

import volume


class TestMicrophoneVolume:
    def test_increase_microphone_volume(self):
        with patch("volume.subprocess.run") as mock_run:
            with patch("volume.send_microphone_osd"):
                volume.increase_microphone_volume(5)

                mock_run.assert_called_once_with(
                    [
                        "pactl",
                        "set-source-volume",
                        "@DEFAULT_SOURCE@",
                        "+5%",
                    ],
                    capture_output=True,
                )

    def test_decrease_microphone_volume(self):
        with patch("volume.subprocess.run") as mock_run:
            with patch("volume.send_microphone_osd"):
                volume.decrease_microphone_volume(5)

                mock_run.assert_called_once_with(
                    [
                        "pactl",
                        "set-source-volume",
                        "@DEFAULT_SOURCE@",
                        "-5%",
                    ],
                    capture_output=True,
                )


class TestToggleMicrophoneMute:
    def test_sends_mic_mute_osd_when_muted(self):
        toggle_result = MagicMock()
        mute_result = MagicMock(stdout="Mute: yes\n")
        osd_result = MagicMock()

        with patch(
            "volume.subprocess.run",
            side_effect=[toggle_result, mute_result, osd_result],
        ) as mock_run:
            volume.toggle_microphone_mute()

            assert mock_run.call_args_list[2] == call(
                ["quickshell-osd-send", "mic-mute", "true"]
            )

    def test_sends_mic_volume_osd_when_unmuted(self):
        toggle_result = MagicMock()
        mute_result = MagicMock(stdout="Mute: no\n")

        with patch(
            "volume.subprocess.run",
            side_effect=[toggle_result, mute_result],
        ):
            with patch("volume.send_microphone_osd") as mock_osd:
                volume.toggle_microphone_mute()
                mock_osd.assert_called_once()


class TestSendMicrophoneOsd:
    def test_sends_mic_volume_percentage(self):
        volume_result = MagicMock(stdout="Volume: front-left: 42000 /  75% / -7.50 dB")
        osd_result = MagicMock()

        with patch(
            "volume.subprocess.run",
            side_effect=[volume_result, osd_result],
        ) as mock_run:
            volume.send_microphone_osd()

            assert mock_run.call_args_list[1] == call(
                ["quickshell-osd-send", "mic", "75"]
            )
