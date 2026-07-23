import json
from unittest.mock import MagicMock, patch

import quickshell_osd_send


class TestWriteJsonToOsdSocket:
    def test_does_nothing_when_socket_file_missing(self):
        with patch("quickshell_osd_send.os.path.exists", return_value=False):
            with patch("quickshell_osd_send.socket.socket") as mock_socket:
                quickshell_osd_send.write_json_to_osd_socket({"type": "volume"})
                mock_socket.assert_not_called()

    def test_sends_json_newline_to_socket(self):
        mock_sock_instance = MagicMock()
        mock_socket_class = MagicMock()
        mock_socket_class.__enter__ = MagicMock(return_value=mock_sock_instance)
        mock_socket_class.__exit__ = MagicMock(return_value=False)

        with patch("quickshell_osd_send.os.path.exists", return_value=True):
            with patch(
                "quickshell_osd_send.socket.socket", return_value=mock_socket_class
            ):
                payload = {"type": "volume", "value": 50, "muted": False}
                quickshell_osd_send.write_json_to_osd_socket(payload)

                mock_sock_instance.connect.assert_called_once()
                sent_data = mock_sock_instance.sendall.call_args[0][0]
                assert sent_data == (json.dumps(payload) + "\n").encode()

    def test_silently_handles_connection_refused(self):
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect.side_effect = ConnectionRefusedError
        mock_socket_class = MagicMock()
        mock_socket_class.__enter__ = MagicMock(return_value=mock_sock_instance)
        mock_socket_class.__exit__ = MagicMock(return_value=False)

        with patch("quickshell_osd_send.os.path.exists", return_value=True):
            with patch(
                "quickshell_osd_send.socket.socket", return_value=mock_socket_class
            ):
                quickshell_osd_send.write_json_to_osd_socket({"type": "volume"})

    def test_silently_handles_os_error(self):
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect.side_effect = OSError("socket error")
        mock_socket_class = MagicMock()
        mock_socket_class.__enter__ = MagicMock(return_value=mock_sock_instance)
        mock_socket_class.__exit__ = MagicMock(return_value=False)

        with patch("quickshell_osd_send.os.path.exists", return_value=True):
            with patch(
                "quickshell_osd_send.socket.socket", return_value=mock_socket_class
            ):
                quickshell_osd_send.write_json_to_osd_socket({"type": "volume"})


class TestSendOsdValueMessage:
    def test_sends_value_message_with_defaults(self):
        with patch("quickshell_osd_send.write_json_to_osd_socket") as mock_write:
            quickshell_osd_send.send_osd_value_message("volume", 75)
            mock_write.assert_called_once_with(
                {"type": "volume", "value": 75, "muted": False}
            )

    def test_sends_value_message_with_muted(self):
        with patch("quickshell_osd_send.write_json_to_osd_socket") as mock_write:
            quickshell_osd_send.send_osd_value_message("mic", 50, muted=True)
            mock_write.assert_called_once_with(
                {"type": "mic", "value": 50, "muted": True}
            )


class TestSendOsdMuteMessage:
    def test_sends_mute_message(self):
        with patch("quickshell_osd_send.write_json_to_osd_socket") as mock_write:
            quickshell_osd_send.send_osd_mute_message("volume", True)
            mock_write.assert_called_once_with(
                {"type": "volume", "value": 0, "muted": True}
            )


class TestMain:
    def test_dispatches_volume_command(self):
        with patch("quickshell_osd_send.send_osd_value_message") as mock_send:
            with patch("quickshell_osd_send.sys.argv", ["cmd", "volume", "80"]):
                quickshell_osd_send.main()
                mock_send.assert_called_once_with("volume", 80)

    def test_dispatches_brightness_command(self):
        with patch("quickshell_osd_send.send_osd_value_message") as mock_send:
            with patch("quickshell_osd_send.sys.argv", ["cmd", "brightness", "50"]):
                quickshell_osd_send.main()
                mock_send.assert_called_once_with("brightness", 50)

    def test_dispatches_mute_command(self):
        with patch("quickshell_osd_send.send_osd_mute_message") as mock_send:
            with patch("quickshell_osd_send.sys.argv", ["cmd", "mute", "true"]):
                quickshell_osd_send.main()
                mock_send.assert_called_once_with("volume", True)

    def test_dispatches_mic_command(self):
        with patch("quickshell_osd_send.send_osd_value_message") as mock_send:
            with patch("quickshell_osd_send.sys.argv", ["cmd", "mic", "30"]):
                quickshell_osd_send.main()
                mock_send.assert_called_once_with("mic", 30)

    def test_dispatches_mic_mute_command(self):
        with patch("quickshell_osd_send.send_osd_mute_message") as mock_send:
            with patch("quickshell_osd_send.sys.argv", ["cmd", "mic-mute", "false"]):
                quickshell_osd_send.main()
                mock_send.assert_called_once_with("mic", False)

    def test_exits_with_error_on_missing_args(self):
        with patch("quickshell_osd_send.sys.argv", ["cmd"]):
            try:
                quickshell_osd_send.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1

    def test_exits_with_error_on_unknown_type(self):
        with patch("quickshell_osd_send.sys.argv", ["cmd", "unknown", "50"]):
            try:
                quickshell_osd_send.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1
