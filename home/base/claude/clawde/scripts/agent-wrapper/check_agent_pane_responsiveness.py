import argparse
import subprocess
import sys
import time

from stuck_indicators import pane_poll_is_stuck_evidence

PANE_CAPTURE_LINE_COUNT = 80
SECONDS_BETWEEN_CAPTURES = 3
HEALTHY_EXIT_CODE = 0
UNRESPONSIVE_EXIT_CODE = 1


def capture_pane_content(tmux_target: str) -> str | None:
    result = subprocess.run(
        [
            "tmux",
            "capture-pane",
            "-p",
            "-t",
            tmux_target,
            "-S",
            f"-{PANE_CAPTURE_LINE_COUNT}",
        ],
        capture_output=True,
        text=True,
    )
    return result.stdout if result.returncode == 0 else None


def determine_pane_health_exit_code(
    first_pane_content: str | None, second_pane_content: str | None
) -> int:
    if second_pane_content is None:
        return HEALTHY_EXIT_CODE
    if pane_poll_is_stuck_evidence(second_pane_content, first_pane_content):
        return UNRESPONSIVE_EXIT_CODE
    return HEALTHY_EXIT_CODE


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="check-agent-pane-responsiveness",
        description="Exit non-zero when a clawde agent's tmux pane is unresponsive: "
        "frozen and not at the idle prompt across two captures, or showing a "
        "usage-limit modal. Captures twice so a working agent that merely mentions "
        "an error is not flagged.",
    )
    parser.add_argument(
        "--tmux-target",
        required=True,
        help="tmux target in session:window form for the agent pane to inspect",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    first_pane_content = capture_pane_content(arguments.tmux_target)
    time.sleep(SECONDS_BETWEEN_CAPTURES)
    second_pane_content = capture_pane_content(arguments.tmux_target)
    sys.exit(determine_pane_health_exit_code(first_pane_content, second_pane_content))


if __name__ == "__main__":
    main()
