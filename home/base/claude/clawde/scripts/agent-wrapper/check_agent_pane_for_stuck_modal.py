import argparse
import subprocess
import sys

from stuck_indicators import pane_indicates_stuck_modal

PANE_CAPTURE_LINE_COUNT = 80
HEALTHY_EXIT_CODE = 0
STUCK_MODAL_EXIT_CODE = 1


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


def determine_pane_health_exit_code(pane_content: str | None) -> int:
    if pane_content is None:
        return HEALTHY_EXIT_CODE
    if pane_indicates_stuck_modal(pane_content):
        return STUCK_MODAL_EXIT_CODE
    return HEALTHY_EXIT_CODE


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="check-agent-pane-for-stuck-modal",
        description="Exit non-zero when a clawde agent's tmux pane shows a stuck modal",
    )
    parser.add_argument(
        "--tmux-target",
        required=True,
        help="tmux target in session:window form for the agent pane to inspect",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    pane_content = capture_pane_content(arguments.tmux_target)
    sys.exit(determine_pane_health_exit_code(pane_content))


if __name__ == "__main__":
    main()
