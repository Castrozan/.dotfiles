import atexit
import os
import subprocess
import time
from pathlib import Path

SESSION_PREFIX = "coached-"

ACTIVE_SESSIONS: list[str] = []
TMUX_SOCKET: str = ""


def cleanup_sessions():
    if not TMUX_SOCKET:
        return
    for session_name in ACTIVE_SESSIONS:
        subprocess.run(
            ["tmux", "-S", TMUX_SOCKET, "kill-session", "-t", session_name],
            capture_output=True,
            timeout=5,
        )


atexit.register(cleanup_sessions)


def discover_tmux_socket() -> str:
    uid = os.getuid()
    for search_path in [f"/run/user/{uid}/tmux-{uid}", f"/tmp/tmux-{uid}"]:
        try:
            for entry in Path(search_path).iterdir():
                if entry.name == "default" and entry.is_socket():
                    return str(entry)
        except (FileNotFoundError, PermissionError):
            continue
    return ""


def run_tmux(socket: str, arguments: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["tmux", "-S", socket] + arguments,
        capture_output=True,
        text=True,
        timeout=10,
    )


def create_session(socket: str, name: str, working_directory: Path) -> str:
    global TMUX_SOCKET
    TMUX_SOCKET = socket
    ACTIVE_SESSIONS.append(name)
    run_tmux(
        socket,
        [
            "new-session",
            "-d",
            "-s",
            name,
            "-n",
            "test",
            "-c",
            str(working_directory),
            "-x",
            "200",
            "-y",
            "50",
        ],
    )
    return f"{name}:test"


def launch_claude(socket: str, target: str, model: str) -> None:
    run_tmux(
        socket,
        [
            "send-keys",
            "-t",
            target,
            f"claude --model {model} --dangerously-skip-permissions",
            "Enter",
        ],
    )


def destroy_session(socket: str, name: str) -> None:
    run_tmux(socket, ["send-keys", "-t", f"{name}:test", "/exit", "Enter"])
    time.sleep(2)
    run_tmux(socket, ["kill-session", "-t", name])
    if name in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS.remove(name)
