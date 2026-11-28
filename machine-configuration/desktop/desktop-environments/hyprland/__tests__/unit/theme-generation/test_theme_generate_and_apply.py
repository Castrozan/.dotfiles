from unittest.mock import MagicMock, patch

import pytest

import theme_generate_and_apply


class TestApplyGeneratedTheme:
    def test_calls_hypr_theme_set_with_theme_name(self):
        with patch("theme_generate_and_apply.subprocess.run") as mock_run:
            theme_generate_and_apply.apply_generated_theme("auto-sunset")

            mock_run.assert_called_once_with(["hypr-theme-set", "auto-sunset"])


class TestMain:
    def test_exits_when_no_arguments(self):
        with patch("theme_generate_and_apply.sys.argv", ["cmd"]):
            with pytest.raises(SystemExit) as exc_info:
                theme_generate_and_apply.main()
            assert exc_info.value.code == 1

    def test_exits_when_image_file_not_found(self, tmp_path):
        missing = tmp_path / "nonexistent.png"
        with patch("theme_generate_and_apply.sys.argv", ["cmd", str(missing)]):
            with pytest.raises(SystemExit) as exc_info:
                theme_generate_and_apply.main()
            assert exc_info.value.code == 1

    def test_generates_and_applies_theme_from_still_or_video(
        self, tmp_path, monkeypatch
    ):
        themes_path = tmp_path / "user-themes"
        themes_path.mkdir()
        monkeypatch.setattr(theme_generate_and_apply, "HYPR_THEMES_PATH", themes_path)
        colors = 'primary = "#aabbcc"\n'

        def check_wallpaper_format(suffix):
            wallpaper = tmp_path / f"sunset-{suffix[1:]}{suffix}"
            wallpaper.write_bytes(b"wallpaper")
            theme_name = f"auto-{wallpaper.stem}"
            theme_dir = themes_path / theme_name
            preview = theme_dir / "preview.png"
            is_video = suffix not in {".png", ".gif"}

            def run(command, **kwargs):
                if command[0] == "ffmpeg":
                    assert command[command.index("-i") + 1] == str(wallpaper)
                    assert command[-1] == str(preview)
                    preview.write_bytes(b"frame")
                elif command[0] == "hypr-theme-generate-from-wallpaper":
                    assert command[1] == str(preview if is_video else wallpaper)
                    if is_video:
                        assert preview.read_bytes() == b"frame"
                    return MagicMock(returncode=0, stdout=colors)
                else:
                    assert command == ["hypr-theme-set", theme_name]
                    assert (theme_dir / "colors.toml").read_text() == colors
                    assert preview.is_file()
                    assert (
                        theme_dir / "backgrounds" / wallpaper.name
                    ).resolve() == wallpaper
                return MagicMock(returncode=0)

            with patch("theme_generate_and_apply.sys.argv", ["cmd", str(wallpaper)]):
                with patch("theme_generate_and_apply.subprocess.run", side_effect=run):
                    theme_generate_and_apply.main()

        for suffix in (".png", ".gif", ".mp4", ".webm", ".mkv", ".mov"):
            check_wallpaper_format(suffix)

    def test_skips_generation_when_cached_theme_still_resolves(
        self, tmp_path, monkeypatch
    ):
        image_file = tmp_path / "sunset.png"
        image_file.write_bytes(b"png")

        themes_path = tmp_path / "user-themes"
        cached_dir = themes_path / "auto-sunset"
        (cached_dir / "backgrounds").mkdir(parents=True)
        (cached_dir / "colors.toml").write_text("cached colors\n")
        (cached_dir / "backgrounds" / "sunset.png").symlink_to(image_file)
        monkeypatch.setattr(theme_generate_and_apply, "HYPR_THEMES_PATH", themes_path)

        with patch("theme_generate_and_apply.sys.argv", ["cmd", str(image_file)]):
            with patch("theme_generate_and_apply.apply_generated_theme") as mock_apply:
                with patch(
                    "theme_generate_and_apply.generate_colors_toml_for_wallpaper"
                ) as mock_gen:
                    theme_generate_and_apply.main()

                    mock_gen.assert_not_called()
                    mock_apply.assert_called_once_with("auto-sunset")

    def test_regenerates_when_cached_background_symlink_dangles(
        self, tmp_path, monkeypatch
    ):
        image_file = tmp_path / "sunset.png"
        image_file.write_bytes(b"png")

        themes_path = tmp_path / "user-themes"
        cached_dir = themes_path / "auto-sunset"
        (cached_dir / "backgrounds").mkdir(parents=True)
        (cached_dir / "colors.toml").write_text("cached colors\n")
        (cached_dir / "backgrounds" / "sunset.png").symlink_to(
            tmp_path / "moved-away.png"
        )
        monkeypatch.setattr(theme_generate_and_apply, "HYPR_THEMES_PATH", themes_path)

        with patch("theme_generate_and_apply.sys.argv", ["cmd", str(image_file)]):
            with patch("theme_generate_and_apply.apply_generated_theme") as mock_apply:
                with patch(
                    "theme_generate_and_apply.generate_colors_toml_for_wallpaper",
                    return_value='primary = "#aabbcc"\n',
                ) as mock_gen:
                    theme_generate_and_apply.main()

                    mock_gen.assert_called_once()
                    mock_apply.assert_called_once_with("auto-sunset")

        background_link = cached_dir / "backgrounds" / "sunset.png"
        assert background_link.resolve() == image_file.resolve()

    def test_regenerates_when_cached_theme_has_no_backgrounds(
        self, tmp_path, monkeypatch
    ):
        image_file = tmp_path / "sunset.png"
        image_file.write_bytes(b"png")

        themes_path = tmp_path / "user-themes"
        cached_dir = themes_path / "auto-sunset"
        cached_dir.mkdir(parents=True)
        (cached_dir / "colors.toml").write_text("cached colors\n")
        monkeypatch.setattr(theme_generate_and_apply, "HYPR_THEMES_PATH", themes_path)

        with patch("theme_generate_and_apply.sys.argv", ["cmd", str(image_file)]):
            with patch("theme_generate_and_apply.apply_generated_theme"):
                with patch(
                    "theme_generate_and_apply.generate_colors_toml_for_wallpaper",
                    return_value='primary = "#aabbcc"\n',
                ) as mock_gen:
                    theme_generate_and_apply.main()

                    mock_gen.assert_called_once()

        assert (cached_dir / "backgrounds" / "sunset.png").is_symlink()
