from unittest.mock import MagicMock, patch

import audio_output_switch


class TestListAllHardwareSinkNames:
    def test_returns_non_monitor_sinks(self):
        mock_result = MagicMock(
            stdout=(
                "0\talsa_output.pci\tmodule\ts32le\t2ch\t48000Hz\tRUNNING\n"
                "1\tbluez_output.bt\tmodule\ts16le\t2ch\t44100Hz\tIDLE\n"
            )
        )

        with patch("audio_output_switch.subprocess.run", return_value=mock_result):
            sinks = audio_output_switch.list_all_hardware_sink_names()
            assert sinks == ["alsa_output.pci", "bluez_output.bt"]

    def test_filters_monitor_sinks(self):
        mock_result = MagicMock(
            stdout=(
                "0\talsa_output.pci\tmodule\ts32le\t2ch\t48000Hz\tRUNNING\n"
                "1\talsa_output.pci.monitor\tmodule\ts32le\t2ch\t48000Hz\tIDLE\n"
            )
        )

        with patch("audio_output_switch.subprocess.run", return_value=mock_result):
            sinks = audio_output_switch.list_all_hardware_sink_names()
            assert sinks == ["alsa_output.pci"]

    def test_returns_empty_when_no_sinks(self):
        mock_result = MagicMock(stdout="")

        with patch("audio_output_switch.subprocess.run", return_value=mock_result):
            sinks = audio_output_switch.list_all_hardware_sink_names()
            assert sinks == []


class TestFindNextSinkInCycle:
    def test_returns_next_sink(self):
        sinks = ["sink_a", "sink_b", "sink_c"]
        assert audio_output_switch.find_next_sink_in_cycle(sinks, "sink_a") == "sink_b"

    def test_wraps_around_to_first(self):
        sinks = ["sink_a", "sink_b", "sink_c"]
        assert audio_output_switch.find_next_sink_in_cycle(sinks, "sink_c") == "sink_a"

    def test_returns_first_when_current_not_found(self):
        sinks = ["sink_a", "sink_b"]
        assert audio_output_switch.find_next_sink_in_cycle(sinks, "unknown") == "sink_a"

    def test_returns_current_when_list_empty(self):
        assert audio_output_switch.find_next_sink_in_cycle([], "sink_a") == "sink_a"

    def test_returns_same_with_single_sink(self):
        assert (
            audio_output_switch.find_next_sink_in_cycle(["only_sink"], "only_sink")
            == "only_sink"
        )


class TestMoveAllPlayingStreamsToSink:
    def test_moves_all_streams(self):
        sinks_result = MagicMock(
            stdout="0\talsa_output.pci\tmodule\ts32le\t2ch\t48000Hz\tRUNNING\n"
        )
        inputs_result = MagicMock(stdout="10\t0\t\t\n11\t0\t\t\n")

        with patch(
            "audio_output_switch.subprocess.run",
            side_effect=[sinks_result, inputs_result, MagicMock(), MagicMock()],
        ) as mock_run:
            audio_output_switch.move_all_playing_streams_to_sink("alsa_output.pci")

            assert mock_run.call_count == 4
            assert mock_run.call_args_list[2][0][0] == [
                "pactl",
                "move-sink-input",
                "10",
                "0",
            ]
            assert mock_run.call_args_list[3][0][0] == [
                "pactl",
                "move-sink-input",
                "11",
                "0",
            ]

    def test_does_nothing_when_sink_not_found(self):
        sinks_result = MagicMock(stdout="")

        with patch(
            "audio_output_switch.subprocess.run",
            side_effect=[sinks_result],
        ) as mock_run:
            audio_output_switch.move_all_playing_streams_to_sink("unknown")
            mock_run.assert_called_once()


class TestGetSinkHumanReadableDescription:
    def test_returns_description(self):
        pactl_output = (
            "Sink #0\n"
            "\tName: alsa_output.pci\n"
            "\tDescription: Built-in Audio Analog Stereo\n"
            "\tDriver: module-alsa-card.c\n"
        )
        mock_result = MagicMock(stdout=pactl_output)

        with patch("audio_output_switch.subprocess.run", return_value=mock_result):
            desc = audio_output_switch.get_sink_human_readable_description(
                "alsa_output.pci"
            )
            assert desc == "Built-in Audio Analog Stereo"

    def test_returns_sink_name_when_not_found(self):
        mock_result = MagicMock(stdout="")

        with patch("audio_output_switch.subprocess.run", return_value=mock_result):
            desc = audio_output_switch.get_sink_human_readable_description(
                "unknown_sink"
            )
            assert desc == "unknown_sink"


class TestSendSinkSwitchNotification:
    def test_sends_notification_with_description(self):
        with patch(
            "audio_output_switch.get_sink_human_readable_description",
            return_value="Built-in Audio",
        ):
            with patch("audio_output_switch.subprocess.run") as mock_run:
                audio_output_switch.send_sink_switch_notification("alsa_output.pci")

                args = mock_run.call_args[0][0]
                assert args[0] == "notify-send"
                assert "Audio Output" in args
                assert "Built-in Audio" in args


class TestMain:
    def test_cycles_to_next_sink(self):
        with patch(
            "audio_output_switch.list_all_hardware_sink_names",
            return_value=["sink_a", "sink_b"],
        ):
            with patch(
                "audio_output_switch.get_default_sink_name",
                return_value="sink_a",
            ):
                with patch("audio_output_switch.set_default_sink") as mock_set:
                    with patch("audio_output_switch.move_all_playing_streams_to_sink"):
                        with patch("audio_output_switch.send_sink_switch_notification"):
                            audio_output_switch.main()
                            mock_set.assert_called_once_with("sink_b")
