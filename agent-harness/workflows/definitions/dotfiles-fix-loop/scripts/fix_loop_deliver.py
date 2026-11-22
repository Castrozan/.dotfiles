import argparse
import json
import sys
from pathlib import Path

from fix_loop_checkout import changed_paths, git, run_program, run_shell

MERGE_ANSWER = "merge"


def held() -> dict:
    return {
        "pushed": False,
        "outcome": "held",
        "detail": "the change stays uncommitted in the checkout for a person",
        "commit": "",
    }


def committed(root: Path, commit_message: str) -> None:
    paths = changed_paths(root)
    if not paths:
        raise SystemExit("the fix loop left nothing to commit")
    for path in paths:
        git(root, "add", "--", path)
    git(root, "commit", "-m", commit_message)


def rebased(root: Path, upstream: str) -> None:
    remote, _, branch = upstream.partition("/")
    git(root, "fetch", remote, branch)
    rebase = run_program(root, ["git", "rebase", upstream])
    if rebase.exit_code == 0:
        return
    run_program(root, ["git", "rebase", "--abort"])
    raise SystemExit(
        f"rebasing onto {upstream} conflicted, so the commit stays local and "
        f"unpushed:\n{rebase.output}"
    )


def delivered(arguments: argparse.Namespace) -> dict:
    root = arguments.root
    committed(root, arguments.commit_message)
    rebased(root, arguments.upstream)
    retested = run_shell(root, arguments.test_command)
    if retested.exit_code:
        raise SystemExit(
            "the scoped test fails after the rebase, so nothing was pushed:\n"
            + retested.output
        )
    remote, _, branch = arguments.upstream.partition("/")
    git(root, "push", remote, f"HEAD:{branch}")
    return {
        "pushed": True,
        "outcome": "pushed",
        "detail": f"pushed fast-forward to {arguments.upstream}",
        "commit": git(root, "rev-parse", "HEAD").strip(),
    }


def parse_command_line(command_line_arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fix-loop-deliver",
        description=(
            "After a person answered merge, commit the changed files, rebase onto "
            "the upstream, rerun the scoped test and push fast-forward only."
        ),
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--answer", required=True)
    parser.add_argument("--test-command", required=True)
    parser.add_argument("--commit-message", required=True)
    parser.add_argument("--upstream", required=True)
    return parser.parse_args(command_line_arguments)


def main() -> int:
    arguments = parse_command_line(sys.argv[1:])
    if arguments.answer != MERGE_ANSWER:
        print(json.dumps(held()))
        return 0
    print(json.dumps(delivered(arguments)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
