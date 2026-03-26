import shutil
import subprocess
import sys
from pathlib import Path

HYPR_THEMES_PATH = Path.home() / ".config" / "hypr-theme" / "user-themes"

NEOVIM_KANAGAWA_COLORSCHEME = """\
return {
\t{ "rebelot/kanagawa.nvim" },
\t{
\t\t"LazyVim/LazyVim",
\t\topts = {
\t\t\tcolorscheme = "kanagawa",
\t\t},
\t},
}
"""

VSCODE_TOKYO_NIGHT_THEME = """\
{
  "name": "Tokyo Night",
  "extension": "enkia.tokyo-night"
}
"""

DEFAULT_ICON_THEME_NAME = "Yaru-purple"


def derive_theme_name_from_image_path(image_path: Path) -> str:
    return f"auto-{image_path.stem}"


def create_theme_directory_structure(theme_directory: Path) -> None:
    theme_directory.mkdir(parents=True, exist_ok=True)
    (theme_directory / "backgrounds").mkdir(exist_ok=True)


def generate_colors_toml_for_wallpaper(image_path: Path) -> str:
    result = subprocess.run(
        ["hypr-theme-generate-from-wallpaper", str(image_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Failed to generate colors: {result.stderr}", file=sys.stderr)
        raise SystemExit(1)
    return result.stdout


def create_preview_image_from_source(
    source_image_path: Path, preview_destination: Path
) -> None:
    if source_image_path.suffix.lower() == ".gif":
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(source_image_path),
                "-vframes",
                "1",
                "-f",
                "image2",
                str(preview_destination),
            ],
            capture_output=True,
        )
    else:
        shutil.copy2(source_image_path, preview_destination)


def symlink_wallpaper_into_backgrounds_directory(
    source_image_path: Path, backgrounds_directory: Path
) -> None:
    link_path = backgrounds_directory / source_image_path.name
    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    link_path.symlink_to(source_image_path.resolve())


def write_theme_configuration_files(
    theme_directory: Path,
    colors_toml_content: str,
    source_image_path: Path,
) -> None:
    (theme_directory / "colors.toml").write_text(colors_toml_content)
    (theme_directory / "icons.theme").write_text(DEFAULT_ICON_THEME_NAME + "\n")
    (theme_directory / "neovim.lua").write_text(NEOVIM_KANAGAWA_COLORSCHEME)
    (theme_directory / "vscode.json").write_text(VSCODE_TOKYO_NIGHT_THEME)
    create_preview_image_from_source(source_image_path, theme_directory / "preview.png")
    symlink_wallpaper_into_backgrounds_directory(
        source_image_path, theme_directory / "backgrounds"
    )


def apply_generated_theme(theme_name: str) -> None:
    subprocess.run(["hypr-theme-set", theme_name])


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: hypr-theme-generate-and-apply <image-path>", file=sys.stderr)
        raise SystemExit(1)

    wallpaper_image_path = Path(sys.argv[1])
    if not wallpaper_image_path.is_file():
        print(f"Image file not found: {wallpaper_image_path}", file=sys.stderr)
        raise SystemExit(1)

    theme_name = derive_theme_name_from_image_path(wallpaper_image_path)
    theme_directory = HYPR_THEMES_PATH / theme_name

    create_theme_directory_structure(theme_directory)
    colors_toml_content = generate_colors_toml_for_wallpaper(wallpaper_image_path)
    write_theme_configuration_files(
        theme_directory, colors_toml_content, wallpaper_image_path
    )
    apply_generated_theme(theme_name)


if __name__ == "__main__":
    main()
