import subprocess
import time
from pathlib import Path

CURRENT_BACKGROUND_LINK = (
    Path.home() / ".config" / "hypr-theme" / "current" / "background"
)


def get_running_swaybg_pids() -> list[str]:
    result = subprocess.run(["pgrep", "swaybg"], capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return result.stdout.strip().split("\n")


def kill_swaybg_pids(pids: list[str]) -> None:
    for pid in pids:
        subprocess.run(["kill", "-9", pid], capture_output=True)


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

    old_pids = get_running_swaybg_pids()
    subprocess.run(
        [
            "hyprctl",
            "dispatch",
            "exec",
            f"swaybg -i '{CURRENT_BACKGROUND_LINK}' -m fill",
        ],
        capture_output=True,
    )
    time.sleep(0.3)
    kill_swaybg_pids(old_pids)


def main() -> None:
    apply_current_background()


if __name__ == "__main__":
    main()
