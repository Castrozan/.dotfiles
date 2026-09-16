from unittest.mock import MagicMock, call, patch
import notification_sound_toggle


class TestIsNotificationSoundMonitorRunning:
    def test_returns_true_when_pid_file_exists_and_process_running(self, tmp_path):
        pid_file = tmp_path / "monitor.pid"
        pid_file.write_text("1234\n")

        with patch.object(
            notification_sound_toggle,
            "NOTIFICATION_SOUND_MONITOR_PID_FILE",
            pid_file,
        ):
            with patch(
                "notification_sound_processes.is_pid_running",
                return_value=True,
            ):
                assert (
                    notification_sound_toggle.is_notification_sound_monitor_running()
                    is True
                )

    def test_returns_false_when_pid_file_missing(self, tmp_path):
        pid_file = tmp_path / "missing.pid"

        with patch.object(
            notification_sound_toggle,
            "NOTIFICATION_SOUND_MONITOR_PID_FILE",
            pid_file,
        ):
            assert (
                notification_sound_toggle.is_notification_sound_monitor_running()
                is False
            )

    def test_returns_false_when_process_not_running(self, tmp_path):
        pid_file = tmp_path / "monitor.pid"
        pid_file.write_text("9999\n")

        with patch.object(
            notification_sound_toggle,
            "NOTIFICATION_SOUND_MONITOR_PID_FILE",
            pid_file,
        ):
            with patch(
                "notification_sound_processes.is_pid_running",
                return_value=False,
            ):
                assert (
                    notification_sound_toggle.is_notification_sound_monitor_running()
                    is False
                )


class TestMuteNotificationSinkInputs:
    def test_mutes_event_role_sink_inputs(self):
        pactl_output = (
            "Sink Input #42\n"
            '    media.role = "event"\n'
            "Sink Input #43\n"
            '    media.role = "music"\n'
        )
        mock_result = MagicMock()
        mock_result.stdout = pactl_output

        with patch(
            "notification_sound_toggle.subprocess.run",
            return_value=mock_result,
        ) as mock_run:
            notification_sound_toggle.mute_notification_sink_inputs()

            assert mock_run.call_count == 2
            assert mock_run.call_args_list[1] == call(
                ["pactl", "set-sink-input-mute", "42", "1"],
                capture_output=True,
            )

    def test_mutes_notification_and_alert_roles(self):
        pactl_output = (
            "Sink Input #10\n"
            '    media.role = "notification"\n'
            "Sink Input #11\n"
            '    media.role = "alert"\n'
        )
        mock_result = MagicMock()
        mock_result.stdout = pactl_output

        with patch(
            "notification_sound_toggle.subprocess.run",
            return_value=mock_result,
        ) as mock_run:
            notification_sound_toggle.mute_notification_sink_inputs()

            assert mock_run.call_count == 3
            assert mock_run.call_args_list[1] == call(
                ["pactl", "set-sink-input-mute", "10", "1"],
                capture_output=True,
            )
            assert mock_run.call_args_list[2] == call(
                ["pactl", "set-sink-input-mute", "11", "1"],
                capture_output=True,
            )

    def test_mutes_canberra_sink_inputs(self):
        pactl_output = "Sink Input #5\n    application.name = libcanberra\n"
        mock_result = MagicMock()
        mock_result.stdout = pactl_output

        with patch(
            "notification_sound_toggle.subprocess.run",
            return_value=mock_result,
        ) as mock_run:
            notification_sound_toggle.mute_notification_sink_inputs()

            assert mock_run.call_count == 2
            assert mock_run.call_args_list[1] == call(
                ["pactl", "set-sink-input-mute", "5", "1"],
                capture_output=True,
            )

    def test_does_nothing_when_no_notification_sink_inputs(self):
        pactl_output = 'Sink Input #1\n    media.role = "music"\n'
        mock_result = MagicMock()
        mock_result.stdout = pactl_output

        with patch(
            "notification_sound_toggle.subprocess.run",
            return_value=mock_result,
        ) as mock_run:
            notification_sound_toggle.mute_notification_sink_inputs()

            mock_run.assert_called_once()


class TestStartNotificationSoundMonitor:
    def test_spawns_bash_process_and_writes_pid(self, tmp_path):
        monitor_pid_file = tmp_path / "monitor.pid"

        mock_process = MagicMock()
        mock_process.pid = 5678

        with patch.object(
            notification_sound_toggle,
            "NOTIFICATION_SOUND_MONITOR_PID_FILE",
            monitor_pid_file,
        ):
            with patch("notification_sound_processes.stop_process_by_pid_file"):
                with patch(
                    "notification_sound_toggle.subprocess.Popen",
                    return_value=mock_process,
                ) as mock_popen:
                    notification_sound_toggle.start_notification_sound_monitor()

                    args = mock_popen.call_args[0][0]
                    assert args[0] == "bash"
                    assert args[1] == "-c"
                    assert "pactl subscribe" in args[2]
                    assert mock_popen.call_args[1]["start_new_session"] is True
                    assert monitor_pid_file.read_text() == "5678"
