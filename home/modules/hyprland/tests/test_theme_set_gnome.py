from unittest.mock import patch

import theme_set_gnome


class TestSetGnomeColorSchemeFromTheme:
    def test_sets_prefer_light_when_light_mode_file_exists(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "light.mode").touch()
        monkeypatch.setattr(theme_set_gnome, "THEME_PATH", theme_path)

        with patch("theme_set_gnome.subprocess.run") as mock_run:
            theme_set_gnome.set_gnome_color_scheme_from_theme()
            mock_run.assert_called_once_with(
                [
                    "gsettings",
                    "set",
                    "org.gnome.desktop.interface",
                    "color-scheme",
                    "prefer-light",
                ]
            )

    def test_sets_prefer_dark_when_no_light_mode_file(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        monkeypatch.setattr(theme_set_gnome, "THEME_PATH", theme_path)

        with patch("theme_set_gnome.subprocess.run") as mock_run:
            theme_set_gnome.set_gnome_color_scheme_from_theme()
            mock_run.assert_called_once_with(
                [
                    "gsettings",
                    "set",
                    "org.gnome.desktop.interface",
                    "color-scheme",
                    "prefer-dark",
                ]
            )


class TestSetGnomeIconThemeFromTheme:
    def test_sets_icon_theme_from_file(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "icons.theme").write_text("Papirus-Dark\n")
        monkeypatch.setattr(theme_set_gnome, "THEME_PATH", theme_path)

        with patch("theme_set_gnome.subprocess.run") as mock_run:
            theme_set_gnome.set_gnome_icon_theme_from_theme()
            mock_run.assert_called_once_with(
                [
                    "gsettings",
                    "set",
                    "org.gnome.desktop.interface",
                    "icon-theme",
                    "Papirus-Dark",
                ]
            )

    def test_does_nothing_when_no_icons_file(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        monkeypatch.setattr(theme_set_gnome, "THEME_PATH", theme_path)

        with patch("theme_set_gnome.subprocess.run") as mock_run:
            theme_set_gnome.set_gnome_icon_theme_from_theme()
            mock_run.assert_not_called()


class TestMain:
    def test_calls_both_gnome_settings(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "icons.theme").write_text("Adwaita\n")
        monkeypatch.setattr(theme_set_gnome, "THEME_PATH", theme_path)

        with patch("theme_set_gnome.subprocess.run") as mock_run:
            theme_set_gnome.main()
            assert mock_run.call_count == 2
            mock_run.assert_any_call(
                [
                    "gsettings",
                    "set",
                    "org.gnome.desktop.interface",
                    "color-scheme",
                    "prefer-dark",
                ]
            )
            mock_run.assert_any_call(
                [
                    "gsettings",
                    "set",
                    "org.gnome.desktop.interface",
                    "icon-theme",
                    "Adwaita",
                ]
            )
