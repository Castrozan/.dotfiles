import theme_set_herdr_accent


class TestReadAccentFromCurrentThemeColors:
    def test_returns_accent_when_present(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "colors.toml").write_text(
            'accent = "#7e9cd8"\nbackground = "#1f1f28"\n'
        )

        monkeypatch.setattr(theme_set_herdr_accent, "CURRENT_THEME_PATH", theme_path)

        assert (
            theme_set_herdr_accent.read_accent_from_current_theme_colors() == "#7e9cd8"
        )

    def test_returns_none_when_colors_missing(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()

        monkeypatch.setattr(theme_set_herdr_accent, "CURRENT_THEME_PATH", theme_path)

        assert theme_set_herdr_accent.read_accent_from_current_theme_colors() is None

    def test_returns_none_when_accent_key_absent(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "colors.toml").write_text('background = "#1f1f28"\n')

        monkeypatch.setattr(theme_set_herdr_accent, "CURRENT_THEME_PATH", theme_path)

        assert theme_set_herdr_accent.read_accent_from_current_theme_colors() is None


class TestRewriteHerdrAccentLine:
    def test_replaces_the_accent_line_only(self):
        config_text = '[ui]\naccent = "@herdr_accent@"\nsidebar_collapsed = true\n'
        result = theme_set_herdr_accent.rewrite_herdr_accent_line(
            config_text, "#7e9cd8"
        )
        assert 'accent = "#7e9cd8"' in result
        assert "sidebar_collapsed = true" in result
        assert "@herdr_accent@" not in result

    def test_leaves_text_unchanged_when_no_accent_line(self):
        config_text = "[ui]\nsidebar_collapsed = true\n"
        assert (
            theme_set_herdr_accent.rewrite_herdr_accent_line(config_text, "#7e9cd8")
            == config_text
        )


class TestUpdateHerdrAccentInConfig:
    def test_rewrites_config_and_reloads(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "colors.toml").write_text('accent = "#7e9cd8"\n')

        herdr_config = tmp_path / "config.toml"
        herdr_config.write_text('[ui]\naccent = "cyan"\n')

        reload_calls = []
        monkeypatch.setattr(theme_set_herdr_accent, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set_herdr_accent, "HERDR_CONFIG", herdr_config)
        monkeypatch.setattr(
            theme_set_herdr_accent,
            "reload_running_herdr_server",
            lambda: reload_calls.append(True),
        )

        theme_set_herdr_accent.update_herdr_accent_in_config()

        assert 'accent = "#7e9cd8"' in herdr_config.read_text()
        assert reload_calls == [True]

    def test_does_nothing_when_herdr_config_missing(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "colors.toml").write_text('accent = "#7e9cd8"\n')

        reload_calls = []
        monkeypatch.setattr(theme_set_herdr_accent, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(
            theme_set_herdr_accent, "HERDR_CONFIG", tmp_path / "missing.toml"
        )
        monkeypatch.setattr(
            theme_set_herdr_accent,
            "reload_running_herdr_server",
            lambda: reload_calls.append(True),
        )

        theme_set_herdr_accent.update_herdr_accent_in_config()

        assert reload_calls == []

    def test_does_not_reload_when_accent_unchanged(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "colors.toml").write_text('accent = "#7e9cd8"\n')

        herdr_config = tmp_path / "config.toml"
        herdr_config.write_text('[ui]\naccent = "#7e9cd8"\n')

        reload_calls = []
        monkeypatch.setattr(theme_set_herdr_accent, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set_herdr_accent, "HERDR_CONFIG", herdr_config)
        monkeypatch.setattr(
            theme_set_herdr_accent,
            "reload_running_herdr_server",
            lambda: reload_calls.append(True),
        )

        theme_set_herdr_accent.update_herdr_accent_in_config()

        assert reload_calls == []
