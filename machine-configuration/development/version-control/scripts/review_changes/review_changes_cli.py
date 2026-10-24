import signal
import sys

from command_runner import ReviewTargetError, run_git
from review_session import review_in_lazygit
from review_target import resolve_review_target


TERMINATING_SIGNALS = (signal.SIGHUP, signal.SIGTERM)


def exit_through_cleanup(signal_number: int, _frame) -> None:
    for terminating_signal in TERMINATING_SIGNALS:
        signal.signal(terminating_signal, signal.SIG_IGN)
    raise SystemExit(128 + signal_number)


def route_terminating_signals_through_cleanup() -> None:
    for terminating_signal in TERMINATING_SIGNALS:
        signal.signal(terminating_signal, exit_through_cleanup)


def prompt_for_target() -> str:
    current_branch = run_git(["branch", "--show-current"])
    return input(f"MR/PR number or branch [{current_branch}]: ")


def main(arguments: list[str]) -> int:
    route_terminating_signals_through_cleanup()
    try:
        raw_target = arguments[0] if arguments else prompt_for_target()
        review_in_lazygit(resolve_review_target(raw_target))
    except ReviewTargetError as error:
        print(f"review-changes: {error}", file=sys.stderr)
        input("Press Enter to close")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
