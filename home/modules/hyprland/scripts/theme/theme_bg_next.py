import subprocess
from pathlib import Path

from theme_bg_apply import send_hyprpaper_ipc_command

WALLPAPERS_DIRECTORY = Path.home() / ".config" / "hypr-theme" / "wallpapers"
CURRENT_BACKGROUND_LINK = (
    Path.home() / ".config" / "hypr-theme" / "current" / "background"
)


def collect_sorted_wallpaper_files() -> list[Path]:
    if not WALLPAPERS_DIRECTORY.is_dir():
        return []

    wallpapers = []
    for entry in sorted(WALLPAPERS_DIRECTORY.iterdir()):
        if entry.is_file() or entry.is_symlink():
            wallpapers.append(entry)

    return sorted(wallpapers, key=lambda path: str(path))


def find_current_wallpaper_index(wallpapers: list[Path]) -> int:
    if not CURRENT_BACKGROUND_LINK.is_symlink():
        return -1
    current_target = CURRENT_BACKGROUND_LINK.readlink()
    for index, wallpaper in enumerate(wallpapers):
        if wallpaper == current_target:
            return index
    return -1


def select_next_wallpaper(wallpapers: list[Path]) -> Path:
    current_index = find_current_wallpaper_index(wallpapers)
    if current_index == -1:
        return wallpapers[0]
    next_index = (current_index + 1) % len(wallpapers)
    return wallpapers[next_index]


def generate_and_apply_theme_from_wallpaper(wallpaper_path: Path) -> None:
    subprocess.run(["hypr-theme-generate-and-apply", str(wallpaper_path)])


def show_no_wallpapers_fallback() -> None:
    subprocess.run(["notify-send", "No wallpapers found", "-t", "2000"])
    send_hyprpaper_ipc_command("unload all")


def main() -> None:
    wallpapers = collect_sorted_wallpaper_files()

    if not wallpapers:
        show_no_wallpapers_fallback()
        return

    next_wallpaper = select_next_wallpaper(wallpapers)
    generate_and_apply_theme_from_wallpaper(next_wallpaper)


if __name__ == "__main__":
    main()
