import signal
from unittest.mock import MagicMock, call, patch

import notification_sound_toggle


class TestIsNotificationSoundsMuted:
    def test_returns_true_when_flag_file_exists(self, tmp_path):
        flag_file = tmp_path / "notification-sounds-muted"
        flag_file.touch()

        with patch.object(
            notification_sound_toggle,
            "NOTIFICATION_SOUNDS_MUTE_FLAG",
            flag_file,
        ):
            assert notification_sound_toggle.is_notification_sounds_muted() is True

    def test_returns_false_when_flag_file_missing(self, tmp_path):
        flag_file = tmp_path / "notification-sounds-muted"

        with patch.object(
            notification_sound_toggle,
            "NOTIFICATION_SOUNDS_MUTE_FLAG",
            flag_file,
        ):
            assert notification_sound_toggle.is_notification_sounds_muted() is False


class TestIsPidRunning:
    def test_returns_true_when_process_exists(self):
        with patch("notification_sound_toggle.os.kill") as mock_kill:
            mock_kill.return_value = None
            assert notification_sound_toggle.is_pid_running(1234) is True
            mock_kill.assert_called_once_with(1234, 0)

    def test_returns_false_when_process_not_found(self):
        with patch(
            "notification_sound_toggle.os.kill",
            side_effect=ProcessLookupError,
        ):
            assert notification_sound_toggle.is_pid_running(9999) is False

    def test_returns_false_when_permission_denied(self):
        with patch(
            "notification_sound_toggle.os.kill",
            side_effect=PermissionError,
        ):
            assert notification_sound_toggle.is_pid_running(1) is False


class TestReadPidFromFile:
    def test_returns_pid_from_valid_file(self, tmp_path):
        pid_file = tmp_path / "test.pid"
        pid_file.write_text("12345\n")

        assert notification_sound_toggle.read_pid_from_file(pid_file) == 12345

    def test_returns_none_when_file_missing(self, tmp_path):
        pid_file = tmp_path / "missing.pid"

        assert notification_sound_toggle.read_pid_from_file(pid_file) is None

    def test_returns_none_when_file_contains_invalid_data(self, tmp_path):
        pid_file = tmp_path / "bad.pid"
        pid_file.write_text("not-a-number\n")

        assert notification_sound_toggle.read_pid_from_file(pid_file) is None


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
                "notification_sound_toggle.is_pid_running",
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
                "notification_sound_toggle.is_pid_running",
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


class TestStopProcessByPidFile:
    def test_kills_process_and_removes_pid_file(self, tmp_path):
        pid_file = tmp_path / "test.pid"
        pid_file.write_text("1234\n")

        with patch("notification_sound_toggle.subprocess.run") as mock_run:
            with patch("notification_sound_toggle.os.kill") as mock_kill:
                notification_sound_toggle.stop_process_by_pid_file(pid_file)

                mock_run.assert_called_once_with(
                    ["pkill", "-P", "1234"],
                    capture_output=True,
                )
                mock_kill.assert_called_once_with(1234, signal.SIGTERM)
                assert not pid_file.exists()

    def test_does_nothing_when_pid_file_missing(self, tmp_path):
        pid_file = tmp_path / "missing.pid"

        with patch("notification_sound_toggle.subprocess.run") as mock_run:
            with patch("notification_sound_toggle.os.kill") as mock_kill:
                notification_sound_toggle.stop_process_by_pid_file(pid_file)

                mock_run.assert_not_called()
                mock_kill.assert_not_called()

    def test_handles_already_dead_process(self, tmp_path):
        pid_file = tmp_path / "test.pid"
        pid_file.write_text("9999\n")

        with patch("notification_sound_toggle.subprocess.run"):
            with patch(
                "notification_sound_toggle.os.kill",
                side_effect=ProcessLookupError,
            ):
                notification_sound_toggle.stop_process_by_pid_file(pid_file)

                assert not pid_file.exists()


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
            with patch("notification_sound_toggle.stop_process_by_pid_file"):
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


class TestStartNotificationSoundDaemon:
    def test_spawns_dbus_monitor_process_and_writes_pid(self, tmp_path):
        daemon_pid_file = tmp_path / "daemon.pid"

        mock_process = MagicMock()
        mock_process.pid = 7890

        with patch.object(
            notification_sound_toggle,
            "NOTIFICATION_SOUND_DAEMON_PID_FILE",
            daemon_pid_file,
        ):
            with patch("notification_sound_toggle.stop_process_by_pid_file"):
                with patch(
                    "notification_sound_toggle.subprocess.Popen",
                    return_value=mock_process,
                ) as mock_popen:
                    notification_sound_toggle.start_notification_sound_daemon()

                    args = mock_popen.call_args[0][0]
                    assert args[0] == "bash"
                    assert args[1] == "-c"
                    assert "dbus-monitor" in args[2]
                    assert mock_popen.call_args[1]["start_new_session"] is True
                    assert daemon_pid_file.read_text() == "7890"


class TestToggleNotificationSounds:
    def test_unmutes_when_currently_muted(self, tmp_path):
        flag_file = tmp_path / "notification-sounds-muted"
        flag_file.touch()

        with patch.object(
            notification_sound_toggle,
            "NOTIFICATION_SOUNDS_MUTE_FLAG",
            flag_file,
        ):
            with patch(
                "notification_sound_toggle.stop_notification_sound_monitor"
            ) as mock_stop:
                notification_sound_toggle.toggle_notification_sounds()

                assert not flag_file.exists()
                mock_stop.assert_called_once()

    def test_mutes_when_currently_unmuted(self, tmp_path):
        flag_file = tmp_path / "notification-sounds-muted"

        with patch.object(
            notification_sound_toggle,
            "NOTIFICATION_SOUNDS_MUTE_FLAG",
            flag_file,
        ):
            with patch(
                "notification_sound_toggle.mute_notification_sink_inputs"
            ) as mock_mute:
                with patch(
                    "notification_sound_toggle.start_notification_sound_monitor"
                ) as mock_start:
                    notification_sound_toggle.toggle_notification_sounds()

                    assert flag_file.exists()
                    mock_mute.assert_called_once()
                    mock_start.assert_called_once()


class TestNotificationSoundStatus:
    def test_prints_muted_status_when_muted(self, tmp_path, capsys):
        flag_file = tmp_path / "notification-sounds-muted"
        flag_file.touch()

        with patch.object(
            notification_sound_toggle,
            "NOTIFICATION_SOUNDS_MUTE_FLAG",
            flag_file,
        ):
            with patch(
                "notification_sound_toggle.ensure_notification_sound_daemon_running"
            ):
                with patch(
                    "notification_sound_toggle.ensure_notification_sound_monitor_running"
                ):
                    notification_sound_toggle.notification_sound_status()

                    output = capsys.readouterr().out
                    assert '"class":"muted"' in output
                    assert "OFF" in output

    def test_prints_on_status_when_unmuted(self, tmp_path, capsys):
        flag_file = tmp_path / "notification-sounds-muted"

        with patch.object(
            notification_sound_toggle,
            "NOTIFICATION_SOUNDS_MUTE_FLAG",
            flag_file,
        ):
            with patch(
                "notification_sound_toggle.ensure_notification_sound_daemon_running"
            ):
                with patch(
                    "notification_sound_toggle.ensure_notification_sound_monitor_running"
                ):
                    notification_sound_toggle.notification_sound_status()

                    output = capsys.readouterr().out
                    assert '"class":"on"' in output
                    assert "ON" in output


class TestMain:
    def test_toggles_when_toggle_argument(self):
        with patch("notification_sound_toggle.sys.argv", ["cmd", "toggle"]):
            with patch(
                "notification_sound_toggle.toggle_notification_sounds"
            ) as mock_toggle:
                notification_sound_toggle.main()

                mock_toggle.assert_called_once()

    def test_shows_status_by_default(self):
        with patch("notification_sound_toggle.sys.argv", ["cmd"]):
            with patch(
                "notification_sound_toggle.notification_sound_status"
            ) as mock_status:
                notification_sound_toggle.main()

                mock_status.assert_called_once()

    def test_shows_status_with_status_argument(self):
        with patch("notification_sound_toggle.sys.argv", ["cmd", "status"]):
            with patch(
                "notification_sound_toggle.notification_sound_status"
            ) as mock_status:
                notification_sound_toggle.main()

                mock_status.assert_called_once()

    def test_exits_with_error_for_unknown_argument(self):
        with patch("notification_sound_toggle.sys.argv", ["cmd", "unknown"]):
            try:
                notification_sound_toggle.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1
