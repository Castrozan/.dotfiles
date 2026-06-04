import time

from coached_tmux import run_tmux


def dismiss_trust_dialog(socket: str, target: str) -> None:
    for _ in range(15):
        result = run_tmux(
            socket,
            [
                "capture-pane",
                "-t",
                target,
                "-p",
                "-S",
                "-20",
            ],
        )
        if "trust this folder" in result.stdout.lower():
            run_tmux(socket, ["send-keys", "-t", target, "Enter"])
            time.sleep(2)
            return
        if "❯" in result.stdout and "trust" not in result.stdout.lower():
            return
        time.sleep(1)


def wait_for_prompt(socket: str, target: str, max_attempts: int = 45) -> bool:
    for attempt in range(max_attempts):
        if attempt == 5:
            dismiss_trust_dialog(socket, target)
        result = run_tmux(
            socket,
            [
                "capture-pane",
                "-t",
                target,
                "-p",
                "-S",
                "-15",
            ],
        )
        if "trust" in result.stdout.lower():
            dismiss_trust_dialog(socket, target)
            continue
        if "❯" in result.stdout:
            return True
        time.sleep(1)
    return False


def send_prompt(socket: str, target: str, text: str) -> None:
    collapsed = " ".join(text.strip().split())
    run_tmux(socket, ["send-keys", "-t", target, collapsed, "Enter"])


def wait_for_completion(
    socket: str,
    target: str,
    prompt_text: str,
    timeout_seconds: int = 300,
) -> bool:
    prompt_fragment = " ".join(prompt_text.strip().split()[:4])
    elapsed = 0.0
    while elapsed < 15.0:
        time.sleep(1.0)
        elapsed += 1.0
        result = run_tmux(
            socket,
            [
                "capture-pane",
                "-t",
                target,
                "-p",
                "-S",
                "-30",
            ],
        )
        if prompt_fragment in result.stdout:
            break

    time.sleep(15)
    elapsed += 15.0

    consecutive_sightings = 0
    while elapsed < timeout_seconds:
        time.sleep(5.0)
        elapsed += 5.0
        result = run_tmux(
            socket,
            [
                "capture-pane",
                "-t",
                target,
                "-p",
                "-S",
                "-10",
            ],
        )
        lines = result.stdout.strip().split("\n")
        found = any(
            line.strip() == "❯" or line.strip().startswith("❯ ") for line in lines
        )
        if found:
            consecutive_sightings += 1
            if consecutive_sightings >= 3:
                return True
        else:
            consecutive_sightings = 0
    return False


def capture_output(socket: str, target: str) -> str:
    result = run_tmux(
        socket,
        [
            "capture-pane",
            "-t",
            target,
            "-p",
            "-S",
            "-99999",
            "-J",
        ],
    )
    return result.stdout
