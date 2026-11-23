import shutil
import subprocess
from pathlib import Path

CURRENT_BACKGROUND_LINK = (
    Path.home() / ".config" / "hypr-theme" / "current" / "background"
)
IMPASTO_SHELL_COMMAND = "impasto-shell"


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

    subprocess.run(
        [
            "awww",
            "img",
            str(CURRENT_BACKGROUND_LINK),
            "--resize",
            "crop",
            "--transition-type",
            "none",
        ],
        capture_output=True,
    )
    hand_background_to_impasto_shell(resolved_background)


def hand_background_to_impasto_shell(background: Path) -> None:
    if shutil.which(IMPASTO_SHELL_COMMAND) is None:
        return

    subprocess.run(
        [
            IMPASTO_SHELL_COMMAND,
            "ipc",
            "--any-display",
            "call",
            "wallpaper",
            "set",
            str(background),
        ],
        capture_output=True,
    )


def main() -> None:
    apply_current_background()


if __name__ == "__main__":
    main()
