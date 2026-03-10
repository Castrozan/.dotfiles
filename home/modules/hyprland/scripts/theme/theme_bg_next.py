import subprocess
import time
from pathlib import Path

THEME_NAME_FILE = Path.home() / ".config" / "hypr-theme" / "current" / "theme.name"
CURRENT_BACKGROUND_LINK = (
    Path.home() / ".config" / "hypr-theme" / "current" / "background"
)


def read_current_theme_name() -> str:
    try:
        return THEME_NAME_FILE.read_text().strip()
    except FileNotFoundError:
        return ""


def collect_sorted_background_files(theme_name: str) -> list[Path]:
    theme_backgrounds_path = (
        Path.home() / ".config" / "hypr-theme" / "current" / "theme" / "backgrounds"
    )
    user_backgrounds_path = (
        Path.home() / ".config" / "hypr-theme" / "backgrounds" / theme_name
    )

    backgrounds = []
    for directory in [user_backgrounds_path, theme_backgrounds_path]:
        if directory.is_dir():
            for entry in sorted(directory.iterdir()):
                if entry.is_file() or entry.is_symlink():
                    backgrounds.append(entry)

    return sorted(backgrounds, key=lambda p: str(p))


def find_current_background_index(backgrounds: list[Path]) -> int:
    if not CURRENT_BACKGROUND_LINK.is_symlink():
        return -1
    current_target = str(CURRENT_BACKGROUND_LINK.readlink())
    for i, background in enumerate(backgrounds):
        if str(background) == current_target:
            return i
    return -1


def select_next_background(backgrounds: list[Path]) -> Path:
    current_index = find_current_background_index(backgrounds)
    if current_index == -1:
        return backgrounds[0]
    next_index = (current_index + 1) % len(backgrounds)
    return backgrounds[next_index]


def set_background_symlink_and_apply(new_background: Path) -> None:
    CURRENT_BACKGROUND_LINK.unlink(missing_ok=True)
    CURRENT_BACKGROUND_LINK.symlink_to(new_background)
    subprocess.run(["hypr-theme-bg-apply"])


def get_running_swaybg_pids() -> list[str]:
    result = subprocess.run(["pgrep", "swaybg"], capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return result.stdout.strip().split("\n")


def kill_swaybg_pids(pids: list[str]) -> None:
    for pid in pids:
        subprocess.run(["kill", "-9", pid], capture_output=True)


def show_no_backgrounds_fallback() -> None:
    subprocess.run(["notify-send", "No background was found for theme", "-t", "2000"])
    old_pids = get_running_swaybg_pids()
    subprocess.run(
        ["hyprctl", "dispatch", "exec", "swaybg --color '#000000'"],
        capture_output=True,
    )
    time.sleep(0.3)
    kill_swaybg_pids(old_pids)


def main() -> None:
    theme_name = read_current_theme_name()
    backgrounds = collect_sorted_background_files(theme_name)

    if not backgrounds:
        show_no_backgrounds_fallback()
        return

    next_background = select_next_background(backgrounds)
    set_background_symlink_and_apply(next_background)


if __name__ == "__main__":
    main()
