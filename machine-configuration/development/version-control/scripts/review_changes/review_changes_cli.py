import shutil
import sys
import tempfile
from pathlib import Path

from command_runner import ReviewTargetError, run_git
from review_session import review_in_lazygit
from review_target import resolve_review_target


def prompt_for_target() -> str:
    current_branch = run_git(["branch", "--show-current"])
    return input(f"MR/PR number or branch [{current_branch}]: ")


def main(arguments: list[str]) -> int:
    review_directory = Path(tempfile.mkdtemp(prefix="review-changes-"))
    try:
        raw_target = arguments[0] if arguments else prompt_for_target()
        review_in_lazygit(resolve_review_target(raw_target), review_directory)
    except ReviewTargetError as error:
        print(f"review-changes: {error}", file=sys.stderr)
        input("Press Enter to close")
        return 1
    finally:
        shutil.rmtree(review_directory, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
