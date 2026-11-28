import json
import shutil
import subprocess
from pathlib import Path

CURRENT_BACKGROUND_LINK = (
    Path.home() / ".config" / "hypr-theme" / "current" / "background"
)
IMPASTO_SHELL_COMMAND = "impasto-shell"
WALLPAPER_COMMAND_TIMEOUT_SECONDS = 10


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

    wallpaper_shown_by_impasto = read_wallpaper_shown_by_impasto_shell()
    if wallpaper_shown_by_impasto is None:
        show_background_with_awww()
        return
    if Path(wallpaper_shown_by_impasto).name == resolved_background.name:
        return
    hand_background_to_impasto_shell(resolved_background)


def show_background_with_awww() -> None:
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
        timeout=WALLPAPER_COMMAND_TIMEOUT_SECONDS,
    )


def run_impasto_wallpaper_list() -> subprocess.CompletedProcess[str] | None:
    if shutil.which(IMPASTO_SHELL_COMMAND) is None:
        return None
    try:
        return subprocess.run(
            [
                IMPASTO_SHELL_COMMAND,
                "ipc",
                "--any-display",
                "call",
                "wallpaper",
                "list",
            ],
            capture_output=True,
            text=True,
            timeout=WALLPAPER_COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def parse_current_wallpaper(wallpaper_list_output: str) -> str | None:
    try:
        return json.loads(wallpaper_list_output).get("current") or ""
    except (json.JSONDecodeError, AttributeError):
        return None


def read_wallpaper_shown_by_impasto_shell() -> str | None:
    result = run_impasto_wallpaper_list()
    if result is None or result.returncode != 0:
        return None
    return parse_current_wallpaper(result.stdout)


def hand_background_to_impasto_shell(background: Path) -> None:
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
        timeout=WALLPAPER_COMMAND_TIMEOUT_SECONDS,
    )


def main() -> None:
    apply_current_background()


if __name__ == "__main__":
    main()
