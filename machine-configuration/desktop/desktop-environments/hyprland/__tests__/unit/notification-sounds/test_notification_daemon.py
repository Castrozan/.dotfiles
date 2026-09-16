from unittest.mock import MagicMock, patch
import notification_sound_toggle


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
            with patch("notification_sound_processes.stop_process_by_pid_file"):
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
