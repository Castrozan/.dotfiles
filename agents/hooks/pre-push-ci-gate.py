#!/usr/bin/env python3

import json
import os
import re
import subprocess
import sys

DOTFILES_REPO_NAME = ".dotfiles"

CI_CHECKS = [
    {
        "name": "statix",
        "cmd": [
            "nix",
            "run",
            "nixpkgs#statix",
            "--",
            "check",
            ".",
            "--ignore",
            "result*",
        ],
    },
    {
        "name": "deadnix",
        "cmd": ["nix", "run", "nixpkgs#deadnix", "--", "."],
    },
    {
        "name": "nixfmt",
        "cmd": [
            "bash",
            "-c",
            "find . -name '*.nix' -not -path './result*' -not -path './.worktrees/*' -not -path './.deep-work/*'"
            " -exec nix run nixpkgs#nixfmt-rfc-style -- --check {} +",
        ],
    },
    {
        "name": "nix flake check",
        "cmd": ["nix", "flake", "check", "--print-build-logs"],
    },
    {
        "name": "quick tests",
        "cmd": ["./tests/run.sh", "--quick"],
    },
    {
        "name": "eval baseline freshness",
        "cmd": ["./agents/evals/run-evals.py", "--check-baseline"],
    },
]

GIT_PUSH_PATTERN = re.compile(
    r"""
    (?:^|&&|\|\||;|\|)\s*   # start of command or chained
    git\s+                   # git command
    (?:\S+\s+)*?             # optional args before subcommand (flags, -C path, etc)
    push\b                   # push subcommand
    """,
    re.VERBOSE,
)


def is_git_push_command(command: str) -> bool:
    return bool(GIT_PUSH_PATTERN.search(command))


def find_repo_root(cwd: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def is_dotfiles_repo(repo_root: str) -> bool:
    return os.path.basename(repo_root) == DOTFILES_REPO_NAME


def run_check(check: dict, repo_root: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            check["cmd"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            timeout=300,
        )
        if result.returncode != 0:
            output = (result.stdout + result.stderr).strip()
            return False, output
        return True, ""
    except subprocess.TimeoutExpired:
        return False, f"{check['name']} timed out (300s)"
    except Exception as e:
        return False, str(e)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not is_git_push_command(command):
        sys.exit(0)

    cwd = data.get("cwd", os.getcwd())
    repo_root = find_repo_root(cwd)

    if not repo_root or not is_dotfiles_repo(repo_root):
        sys.exit(0)

    failures = []

    for check in CI_CHECKS:
        passed, output = run_check(check, repo_root)
        if not passed:
            snippet = output[:500] if output else "(no output)"
            failures.append(f"[{check['name']}] FAILED:\n{snippet}")

    if failures:
        error_report = "\n\n".join(failures)
        print(
            f"PUSH BLOCKED — CI checks failed. Fix these before pushing:\n\n"
            f"{error_report}",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
