import os
import subprocess
import sys
import tempfile
import time

MAX_WAIT_ATTEMPTS = 90
INITIAL_DELAY_SECONDS = 30
REPL_PROMPT_MARKER = "❯"
AUTOSUGGESTION_GHOST_SEPARATOR = "\xa0"
ONBOARDING_INDICATORS = [
    "Select login method",
    "Choose the text style",
    "Paste code here",
    "Claude account with subscription",
]
RESUME_CONFIRMATION_MODAL_INDICATORS = [
    "Resuming the full session will consume",
    "Resume full session as-is",
]


def find_tmux_socket() -> str | None:
    tmux_tmpdir = os.environ.get("TMUX_TMPDIR")
    uid = os.getuid()
    candidate_directories = ([tmux_tmpdir] if tmux_tmpdir else []) + [
        f"/run/user/{uid}/tmux-{uid}",
        f"/tmp/tmux-{uid}",
    ]
    for directory in candidate_directories:
        if os.path.exists(directory):
            socket_path = os.path.join(directory, "default")
            if os.path.exists(socket_path):
                return socket_path
    return None


def run_tmux_command(tmux_socket: str, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["tmux", "-S", tmux_socket, *arguments],
        capture_output=True,
        text=True,
    )


def pane_is_at_onboarding(pane_content: str) -> bool:
    return any(indicator in pane_content for indicator in ONBOARDING_INDICATORS)


def pane_indicates_resume_confirmation_modal(pane_content: str) -> bool:
    return all(
        indicator in pane_content for indicator in RESUME_CONFIRMATION_MODAL_INDICATORS
    )


def send_single_key_to_pane(tmux_socket: str, target: str, key: str) -> bool:
    result = run_tmux_command(tmux_socket, "send-keys", "-t", target, key)
    return result.returncode == 0


def line_is_idle_repl_prompt(line: str) -> bool:
    stripped = line.strip()
    if stripped == REPL_PROMPT_MARKER or stripped.endswith(" " + REPL_PROMPT_MARKER):
        return True
    return line.startswith(REPL_PROMPT_MARKER + AUTOSUGGESTION_GHOST_SEPARATOR)


def pane_is_at_claude_repl_prompt(pane_content: str) -> bool:
    if pane_is_at_onboarding(pane_content):
        return False
    return any(line_is_idle_repl_prompt(line) for line in pane_content.splitlines())


def capture_recent_pane(tmux_socket: str, target: str) -> str | None:
    result = run_tmux_command(
        tmux_socket, "capture-pane", "-t", target, "-p", "-S", "-10"
    )
    return result.stdout if result.returncode == 0 else None


def wait_for_claude_prompt(tmux_socket: str, target: str) -> bool:
    time.sleep(INITIAL_DELAY_SECONDS)

    for _ in range(MAX_WAIT_ATTEMPTS):
        content = capture_recent_pane(tmux_socket, target)
        if content is not None:
            if pane_is_at_onboarding(content):
                time.sleep(5)
                continue
            if pane_is_at_claude_repl_prompt(content):
                return True
        time.sleep(2)
    return False


def pane_is_idle(tmux_socket: str, target: str) -> bool:
    content = capture_recent_pane(tmux_socket, target)
    return content is not None and pane_is_at_claude_repl_prompt(content)


def build_paste_buffer_name(target: str) -> str:
    return f"heartbeat-paste-{target.replace(':', '-')}"


def send_prompt_via_tmux_buffer(tmux_socket: str, target: str, content: str) -> bool:
    buffer_name = build_paste_buffer_name(target)

    with tempfile.NamedTemporaryFile(
        mode="w",
        prefix="heartbeat-prompt-",
        suffix=".md",
        delete=False,
    ) as temporary_file:
        temporary_file.write(content)
        temporary_file_path = temporary_file.name

    try:
        load_result = run_tmux_command(
            tmux_socket, "load-buffer", "-b", buffer_name, temporary_file_path
        )
        if load_result.returncode != 0:
            print(
                f"Error loading buffer: {load_result.stderr.strip()}", file=sys.stderr
            )
            return False

        paste_result = run_tmux_command(
            tmux_socket, "paste-buffer", "-b", buffer_name, "-t", target
        )
        if paste_result.returncode != 0:
            print(
                f"Error pasting buffer: {paste_result.stderr.strip()}", file=sys.stderr
            )
            return False

        run_tmux_command(tmux_socket, "send-keys", "-t", target, "Enter")
        run_tmux_command(tmux_socket, "delete-buffer", "-b", buffer_name)
        return True
    finally:
        os.unlink(temporary_file_path)
