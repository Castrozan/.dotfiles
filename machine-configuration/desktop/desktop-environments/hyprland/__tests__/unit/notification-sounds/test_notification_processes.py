import signal
from unittest.mock import patch
import notification_sound_processes


class TestIsPidRunning:
    def test_returns_true_when_process_exists(self):
        with patch("notification_sound_processes.os.kill") as mock_kill:
            mock_kill.return_value = None
            assert notification_sound_processes.is_pid_running(1234) is True
            mock_kill.assert_called_once_with(1234, 0)

    def test_returns_false_when_permission_denied(self):
        with patch(
            "notification_sound_processes.os.kill",
            side_effect=PermissionError,
        ):
            assert notification_sound_processes.is_pid_running(1) is False


class TestStopProcessByPidFile:
    def test_kills_process_and_removes_pid_file(self, tmp_path):
        pid_file = tmp_path / "test.pid"
        pid_file.write_text("1234\n")

        with patch("notification_sound_processes.subprocess.run") as mock_run:
            with patch("notification_sound_processes.os.kill") as mock_kill:
                notification_sound_processes.stop_process_by_pid_file(pid_file)

                mock_run.assert_called_once_with(
                    ["pkill", "-P", "1234"],
                    capture_output=True,
                )
                mock_kill.assert_called_once_with(1234, signal.SIGTERM)
                assert not pid_file.exists()
