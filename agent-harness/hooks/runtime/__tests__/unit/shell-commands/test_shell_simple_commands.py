import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from hook_module_loader import import_hyphenated_hook_module

shell_simple_commands = import_hyphenated_hook_module("shell_simple_commands")
simple_commands_in = shell_simple_commands.simple_commands_in
words_after_command_wrappers = shell_simple_commands.words_after_command_wrappers


@pytest.mark.parametrize(
    "command_text, expected_simple_commands",
    [
        ("", []),
        ("git status", [["git", "status"]]),
        (
            "git add a.py && git commit -m x; git push | tail -1 || true",
            [
                ["git", "add", "a.py"],
                ["git", "commit", "-m", "x"],
                ["git", "push"],
                ["tail", "-1"],
                ["true"],
            ],
        ),
        ("git status\ngit diff", [["git", "status"], ["git", "diff"]]),
        ("glab mr \\\n  create", [["glab", "mr", "create"]]),
        (
            "git commit -m \"a; b && c\" 'd | e'",
            [["git", "commit", "-m", "a; b && c", "d | e"]],
        ),
        ('echo "a \\" b"', [["echo", 'a " b']]),
        ("echo a\\ b", [["echo", "a b"]]),
        ("glab mr create --title ''", [["glab", "mr", "create", "--title", ""]]),
        ("make 2>&1 &>/tmp/log >&2", [["make", "2>&1", "&>/tmp/log", ">&2"]]),
        ("sleep 1 & wait", [["sleep", "1"], ["wait"]]),
        ("# glab mr create\ngit status # trailing", [["git", "status"]]),
        ("echo a#b", [["echo", "a#b"]]),
        (
            'glab mr create --description "$(cat body.md)" --yes',
            [
                ["cat", "body.md"],
                ["glab", "mr", "create", "--description", "", "--yes"],
            ],
        ),
        ("echo `date` $(pwd)", [["date"], ["pwd"], ["echo", "", ""]]),
        ("(cd /tmp && ls)", [["cd", "/tmp"], ["ls"]]),
        ('echo "(not a subshell)"', [["echo", "(not a subshell)"]]),
        ("echo 'unterminated", [["echo", "unterminated"]]),
    ],
)
def test_splits_command_text_into_simple_commands(
    command_text, expected_simple_commands
):
    assert simple_commands_in(command_text) == expected_simple_commands


@pytest.mark.parametrize(
    "words, expected_invocation_words",
    [
        ([], []),
        (["glab", "mr", "create"], ["glab", "mr", "create"]),
        (["GITLAB_HOST=example.com", "glab", "mr"], ["glab", "mr"]),
        (["env", "A=1", "B=2", "glab", "mr"], ["glab", "mr"]),
        (["rtk", "glab", "mr"], ["glab", "mr"]),
        (["rtk", "proxy", "glab", "mr"], ["glab", "mr"]),
        (["/usr/bin/sudo", "-n", "glab", "mr"], ["glab", "mr"]),
        (["timeout", "-k", "5", "glab", "mr"], ["glab", "mr"]),
        (["timeout", "120", "glab", "mr"], ["glab", "mr"]),
        (["if", "!", "glab", "mr"], ["glab", "mr"]),
        (["echo", "rtk", "glab"], ["echo", "rtk", "glab"]),
        (["A=1"], []),
    ],
)
def test_strips_the_wrappers_in_front_of_the_command(words, expected_invocation_words):
    assert words_after_command_wrappers(words) == expected_invocation_words
