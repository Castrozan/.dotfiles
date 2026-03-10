import subprocess
import time
from pathlib import Path

CURRENT_BACKGROUND_LINK = (
    Path.home() / ".config" / "hypr-theme" / "current" / "background"
)


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

    subprocess.run(["pkill", "-9", "swaybg"], capture_output=True)
    time.sleep(0.3)
    subprocess.run(
        [
            "hyprctl",
            "dispatch",
            "exec",
            f"swaybg -i '{CURRENT_BACKGROUND_LINK}' -m fill",
        ],
        capture_output=True,
    )


def main() -> None:
    apply_current_background()


if __name__ == "__main__":
    main()
