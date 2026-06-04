import atexit
import os
import subprocess
import time
from pathlib import Path

E2E_SESSION_PREFIX = "e2e-test-"

ACTIVE_TEST_SESSIONS: list[str] = []
ACTIVE_TMUX_SOCKET: str = ""


def cleanup_orphaned_test_sessions():
    if not ACTIVE_TMUX_SOCKET:
        return
    for session_name in ACTIVE_TEST_SESSIONS:
        subprocess.run(
            [
                "tmux",
                "-S",
                ACTIVE_TMUX_SOCKET,
                "kill-session",
                "-t",
                session_name,
            ],
            capture_output=True,
            timeout=5,
        )


atexit.register(cleanup_orphaned_test_sessions)


def discover_tmux_socket_path() -> str:
    uid = os.getuid()
    search_paths = [
        f"/run/user/{uid}/tmux-{uid}",
        f"/tmp/tmux-{uid}",
    ]
    for search_path in search_paths:
        try:
            for entry in Path(search_path).iterdir():
                if entry.name == "default" and entry.is_socket():
                    return str(entry)
        except (FileNotFoundError, PermissionError):
            continue
    return ""


def run_tmux_command(
    socket_path: str, tmux_arguments: list[str]
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["tmux", "-S", socket_path] + tmux_arguments,
        capture_output=True,
        text=True,
        timeout=10,
    )


def create_isolated_tmux_session_for_test(
    socket_path: str,
    session_name: str,
    working_directory: Path,
) -> str:
    global ACTIVE_TMUX_SOCKET
    ACTIVE_TMUX_SOCKET = socket_path
    ACTIVE_TEST_SESSIONS.append(session_name)

    run_tmux_command(
        socket_path,
        [
            "new-session",
            "-d",
            "-s",
            session_name,
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
    return f"{session_name}:test"


def launch_claude_in_tmux_session(
    socket_path: str,
    tmux_target: str,
    model: str,
) -> None:
    claude_command = f"claude --model {model} --dangerously-skip-permissions"
    run_tmux_command(
        socket_path,
        ["send-keys", "-t", tmux_target, claude_command, "Enter"],
    )


def destroy_test_session(
    socket_path: str,
    session_name: str,
) -> None:
    run_tmux_command(
        socket_path,
        ["send-keys", "-t", f"{session_name}:test", "C-c", ""],
    )
    time.sleep(1)
    run_tmux_command(
        socket_path,
        ["send-keys", "-t", f"{session_name}:test", "/exit", "Enter"],
    )
    time.sleep(2)
    run_tmux_command(
        socket_path,
        ["kill-session", "-t", session_name],
    )
    if session_name in ACTIVE_TEST_SESSIONS:
        ACTIVE_TEST_SESSIONS.remove(session_name)
