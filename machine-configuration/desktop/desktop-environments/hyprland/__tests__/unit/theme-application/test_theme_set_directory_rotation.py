import theme_set


class TestCopyThemeToNextThemeDirectory:
    def test_copies_theme_directory(self, tmp_path, monkeypatch):
        source = tmp_path / "source-theme"
        source.mkdir()
        (source / "colors.toml").write_text('primary = "#ff0000"\n')
        (source / "bg").mkdir()
        (source / "bg" / "wallpaper.png").write_bytes(b"png")

        next_theme = tmp_path / "next-theme"
        monkeypatch.setattr(theme_set, "NEXT_THEME_PATH", next_theme)

        theme_set.copy_theme_to_next_theme_directory(source)

        assert (next_theme / "colors.toml").read_text() == 'primary = "#ff0000"\n'
        assert (next_theme / "bg" / "wallpaper.png").read_bytes() == b"png"

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


class TestForceRemoveDirectoryTree:
    def test_removes_tree_whose_symlink_dangles(self, tmp_path):
        tree = tmp_path / "old-theme"
        (tree / "backgrounds").mkdir(parents=True)
        (tree / "backgrounds" / "wallpaper.jpg").symlink_to(tmp_path / "moved-away.jpg")

        theme_set.force_remove_directory_tree(tree)

        assert not tree.exists()

    def test_removes_tree_holding_read_only_files(self, tmp_path):
        tree = tmp_path / "old-theme"
        tree.mkdir()
        read_only_file = tree / "colors.toml"
        read_only_file.write_text('accent = "#ffffff"\n')
        read_only_file.chmod(0o444)

        theme_set.force_remove_directory_tree(tree)

        assert not tree.exists()


class TestRotateCurrentThemeWithNext:
    def test_replaces_current_with_next(self, tmp_path, monkeypatch):
        current = tmp_path / "current" / "theme"
        current.mkdir(parents=True)
        (current / "old.txt").write_text("old")

        next_theme = tmp_path / "current" / "next-theme"
        next_theme.mkdir()
        (next_theme / "new.txt").write_text("new")

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", current)
        monkeypatch.setattr(theme_set, "NEXT_THEME_PATH", next_theme)

        theme_set.rotate_current_theme_with_next()

        assert (current / "new.txt").read_text() == "new"
        assert not (current / "old.txt").exists()
        assert not next_theme.exists()

    def test_works_when_no_current_theme(self, tmp_path, monkeypatch):
        current = tmp_path / "current" / "theme"
        (tmp_path / "current").mkdir()

        next_theme = tmp_path / "current" / "next-theme"
        next_theme.mkdir()
        (next_theme / "file.txt").write_text("content")

        monkeypatch.setattr(theme_set, "CURRENT_THEME_PATH", current)
        monkeypatch.setattr(theme_set, "NEXT_THEME_PATH", next_theme)

        theme_set.rotate_current_theme_with_next()

        assert (current / "file.txt").read_text() == "content"

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
