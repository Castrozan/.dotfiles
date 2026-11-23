import theme_set_herdr_accent


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
