import theme_current


class TestReadCurrentThemeName:
    def test_returns_theme_name_from_file(self, tmp_path, monkeypatch):
        theme_name_file = tmp_path / "theme.name"
        theme_name_file.write_text("catppuccin\n")
        monkeypatch.setattr(theme_current, "THEME_NAME_FILE", theme_name_file)
        assert theme_current.read_current_theme_name() == "catppuccin"

    def test_returns_none_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(theme_current, "THEME_NAME_FILE", tmp_path / "missing")
        assert theme_current.read_current_theme_name() == "none"

    def test_strips_whitespace_from_theme_name(self, tmp_path, monkeypatch):
        theme_name_file = tmp_path / "theme.name"
        theme_name_file.write_text("  kanagawa  \n")
        monkeypatch.setattr(theme_current, "THEME_NAME_FILE", theme_name_file)
        assert theme_current.read_current_theme_name() == "kanagawa"
