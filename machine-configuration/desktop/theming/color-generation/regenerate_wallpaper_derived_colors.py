import subprocess
import sys
from pathlib import Path

from theme_generate_from_wallpaper import generate_colors_toml_for_image_path

WALLPAPER_DERIVED_MARKER_FILENAME = "wallpaper-derived.mode"

SUPPORTED_WALLPAPER_IMAGE_SUFFIXES = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
)


def find_wallpaper_derived_theme_directories(themes_directory: Path) -> list[Path]:
    if not themes_directory.is_dir():
        return []
    marker_paths = themes_directory.glob(f"*/{WALLPAPER_DERIVED_MARKER_FILENAME}")
    return sorted(marker_path.parent for marker_path in marker_paths)


def select_active_wallpaper_path(backgrounds_directory: Path) -> Path | None:
    if not backgrounds_directory.is_dir():
        return None
    wallpaper_image_paths = [
        entry
        for entry in backgrounds_directory.iterdir()
        if entry.is_file()
        and entry.suffix.lower() in SUPPORTED_WALLPAPER_IMAGE_SUFFIXES
    ]
    if not wallpaper_image_paths:
        return None
    return min(wallpaper_image_paths, key=lambda path: path.name)


def stage_path_in_repository(dotfiles_directory: Path, path_to_stage: Path) -> None:
    subprocess.run(
        ["git", "-C", str(dotfiles_directory), "add", str(path_to_stage)],
        check=True,
    )


def regenerate_theme_colors_if_wallpaper_palette_changed(
    dotfiles_directory: Path, theme_directory: Path
) -> None:
    active_wallpaper_path = select_active_wallpaper_path(
        theme_directory / "backgrounds"
    )
    if active_wallpaper_path is None:
        return

    colors_toml_path = theme_directory / "colors.toml"
    regenerated_colors_toml = generate_colors_toml_for_image_path(active_wallpaper_path)
    existing_colors_toml = (
        colors_toml_path.read_text() if colors_toml_path.is_file() else None
    )
    if regenerated_colors_toml == existing_colors_toml:
        return

    colors_toml_path.write_text(regenerated_colors_toml)
    stage_path_in_repository(dotfiles_directory, active_wallpaper_path)
    stage_path_in_repository(dotfiles_directory, colors_toml_path)
    print(
        f"theme: regenerated {theme_directory.name}/colors.toml "
        f"from {active_wallpaper_path.name}",
        file=sys.stderr,
    )


def main() -> None:
    dotfiles_directory = Path(
        sys.argv[1] if len(sys.argv) > 1 else Path.home() / ".dotfiles"
    )
    themes_directory = dotfiles_directory / "static" / "themes"

    for theme_directory in find_wallpaper_derived_theme_directories(themes_directory):
        try:
            regenerate_theme_colors_if_wallpaper_palette_changed(
                dotfiles_directory, theme_directory
            )
        except Exception as theme_regeneration_error:
            print(
                f"theme: skipped {theme_directory.name}: {theme_regeneration_error}",
                file=sys.stderr,
            )


if __name__ == "__main__":
    main()
