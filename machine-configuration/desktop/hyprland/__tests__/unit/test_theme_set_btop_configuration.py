import theme_set


class TestUpdateBtopThemeInConfig:
    def test_updates_color_theme_and_background(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        btop_theme = theme_path / "btop.theme"
        btop_theme.write_text("theme content")

        btop_conf = tmp_path / "btop.conf"
        btop_conf.write_text(
            'color_theme = "/old/path/theme"\n'
            "theme_background = True\n"
            "other_setting = value\n"
        )

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set, "BTOP_CONF", btop_conf)

        theme_set.update_btop_theme_in_config()

        content = btop_conf.read_text()
        assert f'color_theme = "{btop_theme}"' in content
        assert "theme_background = False" in content
        assert "other_setting = value" in content

    def test_does_nothing_when_no_btop_conf(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()
        (theme_path / "btop.theme").write_text("theme")

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set, "BTOP_CONF", tmp_path / "nonexistent")

        theme_set.update_btop_theme_in_config()

    def test_does_nothing_when_no_btop_theme(self, tmp_path, monkeypatch):
        theme_path = tmp_path / "theme"
        theme_path.mkdir()

        btop_conf = tmp_path / "btop.conf"
        btop_conf.write_text('color_theme = "old"\n')

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", theme_path)
        monkeypatch.setattr(theme_set, "BTOP_CONF", btop_conf)

        theme_set.update_btop_theme_in_config()

        assert btop_conf.read_text() == 'color_theme = "old"\n'
