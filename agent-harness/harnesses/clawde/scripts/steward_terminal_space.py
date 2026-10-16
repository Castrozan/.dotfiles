import os
import subprocess


def ensure_terminal_space():
    if os.get_terminal_size().lines >= 8:
        return
    pane_identifier = os.environ.get("HERDR_PANE_ID")
    if not pane_identifier:
        raise SystemExit("Collapsed steward terminal requires HERDR_PANE_ID")
    subprocess.run(
        ["herdr", "pane", "zoom", pane_identifier, "--on"],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if os.get_terminal_size().lines < 8:
        raise SystemExit("Steward terminal still has fewer than 8 rows after zoom")


if __name__ == "__main__":
    ensure_terminal_space()
