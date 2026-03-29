import subprocess
from pathlib import Path

CURRENT_BACKGROUND_LINK = (
    Path.home() / ".config" / "hypr-theme" / "current" / "background"
)


def read_currently_loaded_wallpaper_path() -> str | None:
    result = subprocess.run(
        ["hyprctl", "hyprpaper", "listloaded"],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.strip().splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def apply_current_background() -> None:
    if not CURRENT_BACKGROUND_LINK.is_symlink():
        subprocess.run(["notify-send", "No background symlink found", "-t", "2000"])
        raise SystemExit(1)

    resolved_background = CURRENT_BACKGROUND_LINK.resolve()
    if not resolved_background.is_file():
        subprocess.run(
            [
                "notify-send",
                f"Background file not found: {resolved_background}",
                "-t",
                "2000",
            ]
        )
        raise SystemExit(1)

    previous_wallpaper = read_currently_loaded_wallpaper_path()

    wallpaper_path = str(resolved_background)

    subprocess.run(
        ["hyprctl", "hyprpaper", "preload", wallpaper_path],
        capture_output=True,
    )
    subprocess.run(
        ["hyprctl", "hyprpaper", "wallpaper", f",{wallpaper_path}"],
        capture_output=True,
    )

    if previous_wallpaper and previous_wallpaper != wallpaper_path:
        subprocess.run(
            ["hyprctl", "hyprpaper", "unload", previous_wallpaper],
            capture_output=True,
        )


def main() -> None:
    apply_current_background()


if __name__ == "__main__":
    main()
