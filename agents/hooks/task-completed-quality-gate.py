#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


def get_recently_modified_files(cwd: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=5,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.strip().splitlines() if line]


def run_format_check(cwd: str, files: list[str]) -> list[str]:
    failures = []

    nix_files = [f for f in files if f.endswith(".nix")]
    if nix_files:
        for nix_file in nix_files:
            full_path = Path(cwd) / nix_file
            if full_path.exists():
                result = subprocess.run(
                    ["nixfmt", "--check", str(full_path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode != 0:
                    failures.append(
                        f"{nix_file}: nixfmt check failed — run `nixfmt {nix_file}`"
                    )

    python_files = [f for f in files if f.endswith(".py")]
    if python_files:
        result = subprocess.run(
            ["ruff", "check", "--select=E,F,W"] + python_files,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=15,
        )
        if result.returncode != 0:
            failures.append(f"ruff check failed:\n{result.stdout.strip()}")

    shell_files = [f for f in files if f.endswith(".sh")]
    if shell_files:
        for sh_file in shell_files:
            full_path = Path(cwd) / sh_file
            if full_path.exists():
                result = subprocess.run(
                    ["shellcheck", str(full_path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode != 0:
                    failures.append(
                        f"{sh_file}: shellcheck failed:\n{result.stdout.strip()}"
                    )

    return failures


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if data.get("hook_event_name") != "TaskCompleted":
        sys.exit(0)

    cwd = data.get("cwd", ".")
    task_subject = data.get("task_subject", "task")

    try:
        modified_files = get_recently_modified_files(cwd)
    except Exception:
        sys.exit(0)

    if not modified_files:
        sys.exit(0)

    try:
        failures = run_format_check(cwd, modified_files)
    except Exception:
        sys.exit(0)

    if failures:
        failure_summary = "\n".join(failures)
        print(
            f"Formatting issues in '{task_subject}' — fix before marking complete:"
            f"\n{failure_summary}",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
