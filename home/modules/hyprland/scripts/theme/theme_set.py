import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

CURRENT_THEME_PATH = Path.home() / ".config" / "hypr-theme" / "current" / "theme"
NEXT_THEME_PATH = Path.home() / ".config" / "hypr-theme" / "current" / "next-theme"
USER_THEMES_PATH = Path.home() / ".config" / "hypr-theme" / "user-themes"
HYPR_THEMES_PATH = Path.home() / ".config" / "hypr" / "themes"
THEME_NAME_FILE = Path.home() / ".config" / "hypr-theme" / "current" / "theme.name"
BTOP_CONF = Path.home() / ".config" / "btop" / "btop.conf"


def normalize_theme_name(raw_name: str) -> str:
    cleaned = re.sub(r"<[^>]+>", "", raw_name)
    return cleaned.lower().replace(" ", "-")


def find_theme_directory(theme_name: str) -> Path | None:
    for themes_dir in [USER_THEMES_PATH, HYPR_THEMES_PATH]:
        candidate = themes_dir / theme_name
        if candidate.exists():
            return candidate
    return None


def make_directory_tree_writable(directory: Path) -> None:
    for root, dirs, files in os.walk(directory):
        root_path = Path(root)
        root_path.chmod(root_path.stat().st_mode | stat.S_IWUSR)
        for name in files:
            filepath = root_path / name
            filepath.chmod(filepath.stat().st_mode | stat.S_IWUSR)


def copy_theme_to_next_theme_directory(theme_directory: Path) -> None:
    force_remove_directory_tree(NEXT_THEME_PATH)
    shutil.copytree(theme_directory, NEXT_THEME_PATH, symlinks=False)
    make_directory_tree_writable(NEXT_THEME_PATH)


def force_remove_directory_tree(directory: Path) -> None:
    if directory.exists():
        make_directory_tree_writable(directory)
        shutil.rmtree(directory)


def rotate_current_theme_with_next() -> None:
    old_theme_path = CURRENT_THEME_PATH.parent / "old-theme"
    force_remove_directory_tree(old_theme_path)

    if CURRENT_THEME_PATH.exists():
        CURRENT_THEME_PATH.rename(old_theme_path)

    NEXT_THEME_PATH.rename(CURRENT_THEME_PATH)

    force_remove_directory_tree(old_theme_path)


def touch_quickshell_bar_theme_colors_if_present() -> None:
    quickshell_bar_colors = CURRENT_THEME_PATH / "quickshell-bar-colors.json"
    if quickshell_bar_colors.is_file():
        quickshell_bar_colors.touch()


def update_btop_theme_in_config() -> None:
    btop_theme = CURRENT_THEME_PATH / "btop.theme"
    if not BTOP_CONF.is_file() or not btop_theme.is_file():
        return

    content = BTOP_CONF.read_text()
    content = re.sub(
        r"^color_theme = .*$",
        f'color_theme = "{btop_theme}"',
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r"^theme_background = .*$",
        "theme_background = False",
        content,
        flags=re.MULTILINE,
    )
    BTOP_CONF.write_text(content)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: hypr-theme-set <theme-name>", file=sys.stderr)
        raise SystemExit(1)

    theme_name = normalize_theme_name(sys.argv[1])
    theme_directory = find_theme_directory(theme_name)

    if theme_directory is None:
        print(f"Theme '{theme_name}' does not exist", file=sys.stderr)
        raise SystemExit(1)

    copy_theme_to_next_theme_directory(theme_directory)
    subprocess.run(["hypr-theme-set-templates"])
    rotate_current_theme_with_next()
    THEME_NAME_FILE.write_text(theme_name + "\n")
    touch_quickshell_bar_theme_colors_if_present()
    subprocess.run(["hypr-theme-bg-next"])
    subprocess.run(["hypr-restart-hyprctl"])
    subprocess.run(["makoctl", "reload"], capture_output=True)
    update_btop_theme_in_config()
    subprocess.run(["hypr-theme-set-gnome"])
    subprocess.run(["notify-send", "Theme changed", theme_name, "-t", "2000"])


if __name__ == "__main__":
    main()
