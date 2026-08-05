import ast
from pathlib import Path

from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS

HOOK_TESTS_DIRECTORY = Path(__file__).resolve().parent.parent


def python_test_support_files():
    return [
        path
        for path in HOOK_TESTS_DIRECTORY.rglob("*.py")
        if "__pycache__" not in path.parts and path.name != Path(__file__).name
    ]


def hardcoded_timeouts_in(path):
    return [
        (keyword.value.lineno, keyword.value.value)
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg == "timeout"
        and isinstance(keyword.value, ast.Constant)
        and isinstance(keyword.value.value, (int, float))
    ]


def test_no_hook_test_hardcodes_a_subprocess_timeout():
    offenders = [
        f"{path.relative_to(HOOK_TESTS_DIRECTORY)}:{line_number} timeout={value}"
        for path in python_test_support_files()
        for line_number, value in hardcoded_timeouts_in(path)
    ]
    assert not offenders, (
        "hook tests spawn a python interpreter that runs a whole dispatcher, and this "
        "machine routinely runs a nix rebuild in parallel, so a hardcoded timeout turns "
        "an output assertion into a latency assertion and flakes under load. Import "
        "HOOK_SUBPROCESS_TIMEOUT_SECONDS from hook_module_loader instead: "
        f"{offenders}"
    )


def test_shared_timeout_exceeds_the_longest_registered_hook_timeout():
    longest_registered_hook_timeout_seconds = 15
    assert (
        HOOK_SUBPROCESS_TIMEOUT_SECONDS > longest_registered_hook_timeout_seconds * 2
    ), (
        "the shared test timeout must sit well above the longest timeout any hook is "
        "registered with, so a test failure means the dispatcher hung rather than that "
        "the machine was busy"
    )
