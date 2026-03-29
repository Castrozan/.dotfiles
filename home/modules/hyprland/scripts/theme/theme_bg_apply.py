import os
import socket
import subprocess
from pathlib import Path

CURRENT_BACKGROUND_LINK = (
    Path.home() / ".config" / "hypr-theme" / "current" / "background"
)


def find_hyprpaper_socket_path() -> Path | None:
    uid = os.getuid()
    hypr_runtime_directory = Path(f"/run/user/{uid}/hypr")
    if not hypr_runtime_directory.is_dir():
        return None
    for instance_directory in hypr_runtime_directory.iterdir():
        socket_path = instance_directory / ".hyprpaper.sock"
        if socket_path.exists():
            return socket_path
    return None


def send_hyprpaper_ipc_command(command: str) -> str:
    socket_path = find_hyprpaper_socket_path()
    if socket_path is None:
        return ""
    hyprpaper_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        hyprpaper_socket.connect(str(socket_path))
        hyprpaper_socket.send(command.encode())
        return hyprpaper_socket.recv(8192).decode()
    finally:
        hyprpaper_socket.close()


def read_currently_loaded_wallpaper_path() -> str | None:
    response = send_hyprpaper_ipc_command("listloaded")
    for line in response.strip().splitlines():
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

    send_hyprpaper_ipc_command(f"preload {wallpaper_path}")
    send_hyprpaper_ipc_command(f"wallpaper ,{wallpaper_path}")

    if previous_wallpaper and previous_wallpaper != wallpaper_path:
        send_hyprpaper_ipc_command(f"unload {previous_wallpaper}")


def main() -> None:
    apply_current_background()


if __name__ == "__main__":
    main()
