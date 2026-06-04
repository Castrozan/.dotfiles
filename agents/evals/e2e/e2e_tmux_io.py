import time

from e2e_tmux import run_tmux_command


def dismiss_workspace_trust_dialog_if_present(
    socket_path: str,
    tmux_target: str,
) -> None:
    for _ in range(15):
        result = run_tmux_command(
            socket_path,
            [
                "capture-pane",
                "-t",
                tmux_target,
                "-p",
                "-S",
                "-20",
            ],
        )
        captured_text = result.stdout
        if "trust this folder" in captured_text.lower():
            run_tmux_command(
                socket_path,
                [
                    "send-keys",
                    "-t",
                    tmux_target,
                    "Enter",
                ],
            )
            time.sleep(2)
            return
        if "❯" in captured_text and "trust" not in captured_text.lower():
            return
        time.sleep(1)


def wait_for_claude_input_prompt_indicator(
    socket_path: str,
    tmux_target: str,
    max_attempts: int = 45,
    interval_seconds: float = 1.0,
) -> bool:
    for attempt in range(max_attempts):
        if attempt == 5:
            dismiss_workspace_trust_dialog_if_present(socket_path, tmux_target)

        result = run_tmux_command(
            socket_path,
            [
                "capture-pane",
                "-t",
                tmux_target,
                "-p",
                "-S",
                "-15",
            ],
        )
        captured_text = result.stdout

        if "trust" in captured_text.lower():
            dismiss_workspace_trust_dialog_if_present(socket_path, tmux_target)
            continue

        if "❯" in captured_text:
            return True

        time.sleep(interval_seconds)
    return False


def send_prompt_to_claude_session(
    socket_path: str,
    tmux_target: str,
    prompt_text: str,
) -> None:
    collapsed_prompt = " ".join(prompt_text.strip().split())
    run_tmux_command(
        socket_path,
        [
            "send-keys",
            "-t",
            tmux_target,
            collapsed_prompt,
            "Enter",
        ],
    )


def capture_last_lines(
    socket_path: str,
    tmux_target: str,
    line_count: int = 20,
) -> str:
    result = run_tmux_command(
        socket_path,
        [
            "capture-pane",
            "-t",
            tmux_target,
            "-p",
            "-S",
            f"-{line_count}",
        ],
    )
    return result.stdout


def wait_for_response_completion(
    socket_path: str,
    tmux_target: str,
    prompt_text: str,
    timeout_seconds: int = 300,
    poll_interval_seconds: float = 5.0,
) -> bool:
    prompt_words = prompt_text.strip().split()[:4]
    prompt_fragment = " ".join(prompt_words)

    elapsed = 0.0
    while elapsed < 15.0:
        time.sleep(1.0)
        elapsed += 1.0
        captured = capture_last_lines(socket_path, tmux_target, 30)
        if prompt_fragment in captured:
            break

    time.sleep(15)
    elapsed += 15.0

    consecutive_prompt_sightings = 0
    required_consecutive_sightings = 3

    while elapsed < timeout_seconds:
        time.sleep(poll_interval_seconds)
        elapsed += poll_interval_seconds
        captured = capture_last_lines(socket_path, tmux_target, 10)
        lines = captured.strip().split("\n")
        prompt_found_this_poll = False
        for line in lines:
            stripped = line.strip()
            if stripped == "❯" or stripped.startswith("❯ "):
                prompt_found_this_poll = True
                break

        if prompt_found_this_poll:
            consecutive_prompt_sightings += 1
            if consecutive_prompt_sightings >= required_consecutive_sightings:
                return True
        else:
            consecutive_prompt_sightings = 0
    return False


def capture_full_terminal_output(
    socket_path: str,
    tmux_target: str,
) -> str:
    result = run_tmux_command(
        socket_path,
        [
            "capture-pane",
            "-t",
            tmux_target,
            "-p",
            "-S",
            "-99999",
            "-J",
        ],
    )
    return result.stdout
