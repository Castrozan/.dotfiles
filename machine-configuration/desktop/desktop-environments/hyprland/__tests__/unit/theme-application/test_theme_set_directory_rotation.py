import theme_set


class TestCopyThemeToNextThemeDirectory:
    def test_removes_existing_next_theme_before_copy(self, tmp_path, monkeypatch):
        source = tmp_path / "source"
        source.mkdir()
        (source / "new.txt").write_text("new")

        next_theme = tmp_path / "next-theme"
        next_theme.mkdir()
        (next_theme / "old.txt").write_text("old")

        monkeypatch.setattr(theme_set, "NEXT_THEME_PATH", next_theme)

        theme_set.copy_theme_to_next_theme_directory(source)

        assert not (next_theme / "old.txt").exists()
        assert (next_theme / "new.txt").read_text() == "new"

    def test_copies_theme_whose_background_symlink_dangles(self, tmp_path, monkeypatch):
        source = tmp_path / "source-theme"
        (source / "backgrounds").mkdir(parents=True)
        (source / "backgrounds" / "wallpaper.jpg").symlink_to(
            tmp_path / "moved-away.jpg"
        )

        next_theme = tmp_path / "next-theme"
        monkeypatch.setattr(theme_set, "NEXT_THEME_PATH", next_theme)

        theme_set.copy_theme_to_next_theme_directory(source)

        assert (next_theme / "backgrounds" / "wallpaper.jpg").is_symlink()


class TestRotateCurrentThemeWithNext:
    def test_rotates_out_a_current_theme_whose_background_dangles(
        self, tmp_path, monkeypatch
    ):
        current = tmp_path / "current" / "theme"
        (current / "backgrounds").mkdir(parents=True)
        (current / "backgrounds" / "retired.jpg").symlink_to(
            tmp_path / "moved-away.jpg"
        )

        next_theme = tmp_path / "current" / "next-theme"
        (next_theme / "backgrounds").mkdir(parents=True)
        (next_theme / "colors.toml").write_text('accent = "#e44545"\n')

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", current)
        monkeypatch.setattr(theme_set, "NEXT_THEME_PATH", next_theme)

        theme_set.rotate_current_theme_with_next()

        assert (current / "colors.toml").read_text() == 'accent = "#e44545"\n'
        assert not (current / "backgrounds" / "retired.jpg").is_symlink()
        assert not (tmp_path / "current" / "old-theme").exists()
