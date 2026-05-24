import json
from unittest.mock import MagicMock, patch

import microphone_toggle


class TestGetMicrophoneMuteStatus:
    def test_returns_muted_when_pactl_says_yes(self):
        mock_result = MagicMock()
        mock_result.stdout = "Mute: yes"

        with patch("microphone_toggle.subprocess.run", return_value=mock_result):
            assert microphone_toggle.get_microphone_mute_status() == "muted"

    def test_returns_unmuted_when_pactl_says_no(self):
        mock_result = MagicMock()
        mock_result.stdout = "Mute: no"

        with patch("microphone_toggle.subprocess.run", return_value=mock_result):
            assert microphone_toggle.get_microphone_mute_status() == "unmuted"


class TestGetMicrophoneVolume:
    def test_parses_volume_percentage(self):
        mock_result = MagicMock()
        mock_result.stdout = (
            "Volume: front-left: 32768 /  50% / -18.06 dB,"
            "   front-right: 32768 /  50% / -18.06 dB"
        )

        with patch("microphone_toggle.subprocess.run", return_value=mock_result):
            assert microphone_toggle.get_microphone_volume() == "50"

    def test_returns_zero_when_no_percentage_found(self):
        mock_result = MagicMock()
        mock_result.stdout = "No volume info"

        with patch("microphone_toggle.subprocess.run", return_value=mock_result):
            assert microphone_toggle.get_microphone_volume() == "0"


class TestOutputMicrophoneStatusJson:
    def test_outputs_muted_json(self, capsys):
        with patch(
            "microphone_toggle.get_microphone_mute_status",
            return_value="muted",
        ):
            with patch(
                "microphone_toggle.get_microphone_volume",
                return_value="50",
            ):
                microphone_toggle.output_microphone_status_json()

        output = json.loads(capsys.readouterr().out.strip())
        assert output["tooltip"] == "Microphone MUTED"
        assert output["class"] == "muted"

    def test_outputs_unmuted_json_with_volume(self, capsys):
        with patch(
            "microphone_toggle.get_microphone_mute_status",
            return_value="unmuted",
        ):
            with patch(
                "microphone_toggle.get_microphone_volume",
                return_value="75",
            ):
                microphone_toggle.output_microphone_status_json()

        output = json.loads(capsys.readouterr().out.strip())
        assert output["tooltip"] == "Microphone unmuted (75%)"
        assert output["class"] == "unmuted"


class TestToggleMicrophoneMute:
    def test_calls_pactl_toggle(self):
        with patch("microphone_toggle.subprocess.run") as mock_run:
            microphone_toggle.toggle_microphone_mute()
            mock_run.assert_called_once_with(
                [
                    "pactl",
                    "set-source-mute",
                    "@DEFAULT_SOURCE@",
                    "toggle",
                ],
                capture_output=True,
            )


class TestMain:
    def test_status_action(self):
        with patch("microphone_toggle.output_microphone_status_json") as mock_output:
            with patch("microphone_toggle.sys.argv", ["cmd", "status"]):
                microphone_toggle.main()
                mock_output.assert_called_once()

    def test_toggle_action(self):
        with patch("microphone_toggle.toggle_microphone_mute") as mock_toggle:
            with patch("microphone_toggle.sys.argv", ["cmd", "toggle"]):
                microphone_toggle.main()
                mock_toggle.assert_called_once()

    def test_default_action_is_status(self):
        with patch("microphone_toggle.output_microphone_status_json") as mock_output:
            with patch("microphone_toggle.sys.argv", ["cmd"]):
                microphone_toggle.main()
                mock_output.assert_called_once()

    def test_unknown_action_exits_with_error(self):
        with patch("microphone_toggle.sys.argv", ["cmd", "unknown"]):
            try:
                microphone_toggle.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1
