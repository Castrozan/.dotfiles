#!/usr/bin/env python3
"""Empirically classify background-bash command patterns and assert the hook's
static hang detectors agree with real runtime behavior.

Run patterns under setsid (start_new_session=True) with stdin at EOF, which
faithfully replicates the Claude Code background-bash environment (no
controlling terminal, stdin returns EOF immediately). For each pattern we
compare three things:

  * empirical runtime behavior   - does it terminate on its own, or hang?
  * the hook's static prediction - would background_bash_hang_detectors deny it?
  * the intended policy           - deny, or allow?

This is the regression check behind the deny rules: if a tool upgrade changes
behavior (a pager that starts paging, a git that stops opening an editor), the
empirical column drifts and this harness exits non-zero so the cron can alert.
"""

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pre-tool-use"))

from interactive_command_hang_detectors import (  # noqa: E402
    command_launches_interactive_full_screen_program,
    command_runs_git_subcommand_that_opens_an_editor,
)

TERMINATION_DEADLINE_SECONDS = 4


def hook_would_deny(command_string):
    return command_launches_interactive_full_screen_program(
        command_string
    ) or command_runs_git_subcommand_that_opens_an_editor(command_string)


def first_program_word(command_string):
    for token in command_string.split():
        if "=" in token and not token.startswith("-"):
            continue
        return token
    return command_string


def program_is_installed(command_string):
    program = first_program_word(command_string)
    if program in {"while", "for", "if", "read", ":", "git"}:
        return True
    return shutil.which(program) is not None


def empirically_hangs(command_string, working_directory=None):
    try:
        subprocess.run(
            ["bash", "-c", command_string],
            cwd=working_directory,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            timeout=TERMINATION_DEADLINE_SECONDS,
        )
        return False
    except subprocess.TimeoutExpired:
        return True


SHOULD_HANG_AND_BE_DENIED = (
    "vim notes.txt",
    "vi /etc/hosts",
    "nvim",
    "nano /etc/hosts",
    "top",
)

SHOULD_TERMINATE_AND_BE_ALLOWED = (
    "echo hello",
    "less /etc/hosts",
    "more /etc/hosts",
    "man ls",
    "cat /etc/hosts",
    "python3 -u -c 'print(1)'",
)

HANGS_BUT_INTENTIONALLY_ALLOWED = (
    "tail -f /dev/null",
    "sleep 600",
)


def check_category(label, commands, expect_hang, expect_deny):
    mismatches = []
    for command_string in commands:
        if not program_is_installed(command_string):
            print(f"  SKIP (not installed)        | {command_string}")
            continue
        actual_hang = empirically_hangs(command_string)
        actual_deny = hook_would_deny(command_string)
        ok = actual_hang == expect_hang and actual_deny == expect_deny
        marker = "OK  " if ok else "FAIL"
        print(
            f"  {marker} hang={actual_hang!s:5} deny={actual_deny!s:5} "
            f"(want hang={expect_hang!s:5} deny={expect_deny!s:5}) | {command_string}"
        )
        if not ok:
            mismatches.append(command_string)
    if mismatches:
        print(f"[{label}] {len(mismatches)} mismatch(es): {mismatches}")
    return mismatches


def main():
    all_mismatches = []
    print("== should hang AND be denied ==")
    all_mismatches += check_category(
        "hang-and-deny", SHOULD_HANG_AND_BE_DENIED, expect_hang=True, expect_deny=True
    )
    print("== should terminate AND be allowed ==")
    all_mismatches += check_category(
        "terminate-and-allow",
        SHOULD_TERMINATE_AND_BE_ALLOWED,
        expect_hang=False,
        expect_deny=False,
    )
    print("== hangs by design BUT intentionally allowed (legit background) ==")
    all_mismatches += check_category(
        "hang-but-allow",
        HANGS_BUT_INTENTIONALLY_ALLOWED,
        expect_hang=True,
        expect_deny=False,
    )
    if all_mismatches:
        print(f"\nDRIFT DETECTED: {len(all_mismatches)} pattern(s) no longer match.")
        sys.exit(1)
    print("\nAll background-bash hang classifications match the hook detectors.")


if __name__ == "__main__":
    main()
