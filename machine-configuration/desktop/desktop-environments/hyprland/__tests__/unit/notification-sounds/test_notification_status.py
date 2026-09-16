from unittest.mock import patch
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
