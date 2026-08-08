from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import theme_generate_and_apply


class TestCreateThemeDirectoryStructure:
    def test_creates_theme_and_backgrounds_directories(self, tmp_path):
        theme_dir = tmp_path / "auto-test"
        theme_generate_and_apply.create_theme_directory_structure(theme_dir)

        assert theme_dir.is_dir()
        assert (theme_dir / "backgrounds").is_dir()

    def test_is_idempotent(self, tmp_path):
        theme_dir = tmp_path / "auto-test"
        theme_generate_and_apply.create_theme_directory_structure(theme_dir)
        theme_generate_and_apply.create_theme_directory_structure(theme_dir)

        assert theme_dir.is_dir()
        assert (theme_dir / "backgrounds").is_dir()


class TestGenerateColorsTomlForWallpaper:
    def test_returns_stdout_on_success(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'primary = "#7aa2f7"\n'

        with patch(
            "theme_generate_and_apply.subprocess.run",
            return_value=mock_result,
        ) as mock_run:
            result = theme_generate_and_apply.generate_colors_toml_for_wallpaper(
                Path("/wallpapers/sunset.png")
            )

            assert result == 'primary = "#7aa2f7"\n'
            mock_run.assert_called_once_with(
                ["hypr-theme-generate-from-wallpaper", "/wallpapers/sunset.png"],
                capture_output=True,
                text=True,
            )

    def test_exits_on_failure(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "generation failed"

        with patch(
            "theme_generate_and_apply.subprocess.run",
            return_value=mock_result,
        ):
            with pytest.raises(SystemExit) as exc_info:
                theme_generate_and_apply.generate_colors_toml_for_wallpaper(
                    Path("/wallpapers/broken.png")
                )

            assert exc_info.value.code == 1


class TestCreatePreviewImageFromSource:
    def test_copies_non_gif_image_directly(self, tmp_path):
        source = tmp_path / "wall.png"
        source.write_bytes(b"fake-png-data")
        preview = tmp_path / "preview.png"

        theme_generate_and_apply.create_preview_image_from_source(source, preview)

        assert preview.read_bytes() == b"fake-png-data"

    def test_extracts_first_frame_from_gif_via_ffmpeg(self, tmp_path):
        source = tmp_path / "anim.gif"
        source.write_bytes(b"fake-gif")
        preview = tmp_path / "preview.png"

        with patch("theme_generate_and_apply.subprocess.run") as mock_run:
            theme_generate_and_apply.create_preview_image_from_source(source, preview)

            mock_run.assert_called_once_with(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(source),
                    "-vframes",
                    "1",
                    "-f",
                    "image2",
                    str(preview),
                ],
                capture_output=True,
            )

    def test_handles_uppercase_gif_extension(self, tmp_path):
        source = tmp_path / "anim.GIF"
        source.write_bytes(b"fake-gif")
        preview = tmp_path / "preview.png"

        with patch("theme_generate_and_apply.subprocess.run") as mock_run:
            theme_generate_and_apply.create_preview_image_from_source(source, preview)

            mock_run.assert_called_once()


class TestSymlinkWallpaperIntoBackgroundsDirectory:
    def test_creates_symlink_to_source_image(self, tmp_path):
        source = tmp_path / "source" / "wall.png"
        source.parent.mkdir()
        source.write_bytes(b"img")
        backgrounds = tmp_path / "backgrounds"
        backgrounds.mkdir()

        theme_generate_and_apply.symlink_wallpaper_into_backgrounds_directory(
            source, backgrounds
        )

        link = backgrounds / "wall.png"
        assert link.is_symlink()
        assert link.resolve() == source.resolve()

    def test_replaces_existing_symlink(self, tmp_path):
        old_target = tmp_path / "old.png"
        old_target.write_bytes(b"old")
        source = tmp_path / "new.png"
        source.write_bytes(b"new")

        backgrounds = tmp_path / "backgrounds"
        backgrounds.mkdir()
        (backgrounds / "new.png").symlink_to(old_target)

        theme_generate_and_apply.symlink_wallpaper_into_backgrounds_directory(
            source, backgrounds
        )

        link = backgrounds / "new.png"
        assert link.resolve() == source.resolve()

    def test_replaces_a_symlink_whose_target_moved_away(self, tmp_path):
        source = tmp_path / "wall.png"
        source.write_bytes(b"img")

        backgrounds = tmp_path / "backgrounds"
        backgrounds.mkdir()
        (backgrounds / "wall.png").symlink_to(tmp_path / "moved-away.png")

        theme_generate_and_apply.symlink_wallpaper_into_backgrounds_directory(
            source, backgrounds
        )

        link = backgrounds / "wall.png"
        assert link.resolve() == source.resolve()


class TestWriteThemeConfigurationFiles:
    def test_writes_all_configuration_files(self, tmp_path):
        theme_dir = tmp_path / "theme"
        theme_dir.mkdir()
        (theme_dir / "backgrounds").mkdir()

        source_image = tmp_path / "wall.png"
        source_image.write_bytes(b"png-data")

        theme_generate_and_apply.write_theme_configuration_files(
            theme_dir, 'primary = "#ff0000"\n', source_image
        )

        assert (theme_dir / "colors.toml").read_text() == 'primary = "#ff0000"\n'
        assert (theme_dir / "icons.theme").read_text() == "Yaru-purple\n"
        assert "kanagawa" in (theme_dir / "neovim.lua").read_text()
        assert "Tokyo Night" in (theme_dir / "vscode.json").read_text()
        assert (theme_dir / "preview.png").read_bytes() == b"png-data"
        assert (theme_dir / "backgrounds" / "wall.png").is_symlink()
