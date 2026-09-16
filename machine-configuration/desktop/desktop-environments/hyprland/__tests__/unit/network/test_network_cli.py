from unittest.mock import patch
import network


class TestMain:
    def test_opens_settings_with_full_flag(self):
        with patch("network.sys.argv", ["cmd", "--full"]):
            with patch("network.subprocess.Popen") as mock_popen:
                network.main()

                mock_popen.assert_called_once_with(
                    ["nm-connection-editor"],
                    start_new_session=True,
                )

    def test_shows_main_menu_without_args(self):
        with patch("network.sys.argv", ["cmd"]):
            with patch("network.show_main_menu") as mock_menu:
                network.main()
                mock_menu.assert_called_once()
