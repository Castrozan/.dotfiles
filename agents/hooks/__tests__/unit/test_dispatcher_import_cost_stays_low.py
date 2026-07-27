import ast
import subprocess
import sys
from pathlib import Path

from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS

HOOKS_ROOT = Path(__file__).resolve().parents[2]
HOOK_DISPATCH_SOURCE = HOOKS_ROOT / "common" / "hook_dispatch.py"

DISPATCHER_SOURCES = [
    next(HOOKS_ROOT.rglob(dispatcher_name))
    for dispatcher_name in (
        "pre-tool-use-dispatcher.py",
        "post-tool-use-dispatcher.py",
        "stop-dispatcher.py",
        "session-start-dispatcher.py",
        "user-prompt-submit-dispatcher.py",
    )
]

MODULES_TOO_EXPENSIVE_FOR_EVERY_TOOL_CALL = {"dataclasses", "typing", "inspect"}


def module_level_imports_of(path):
    tree = ast.parse(path.read_text())
    imported = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def test_hook_dispatch_avoids_the_expensive_stdlib_modules():
    offenders = module_level_imports_of(HOOK_DISPATCH_SOURCE) & (
        MODULES_TOO_EXPENSIVE_FOR_EVERY_TOOL_CALL
    )
    assert not offenders, (
        "hook_dispatch is imported by every dispatcher on every tool call, and "
        "dataclasses drags in inspect, dis, ast and tokenize for machinery these "
        "small carrier classes never use; measured, dropping it cut a PreToolUse "
        f"invocation from 85ms to 54ms. Replace with plain classes: {sorted(offenders)}"
    )


def test_no_dispatcher_imports_the_expensive_stdlib_modules():
    offenders = {
        str(path.relative_to(HOOKS_ROOT)): sorted(
            module_level_imports_of(path) & MODULES_TOO_EXPENSIVE_FOR_EVERY_TOOL_CALL
        )
        for path in DISPATCHER_SOURCES
        if module_level_imports_of(path) & MODULES_TOO_EXPENSIVE_FOR_EVERY_TOOL_CALL
    }
    assert not offenders, (
        "a dispatcher runs as a fresh interpreter on every matching tool call, so a "
        f"module-level import of these costs real latency every time: {offenders}"
    )


def test_hook_dispatch_carrier_classes_survive_without_dataclasses():
    program = (
        f"import sys; sys.path.insert(0, {str(HOOK_DISPATCH_SOURCE.parent)!r});"
        "import hook_dispatch as d;"
        "r = d.HandlerResult(decision='deny', reason='x');"
        "h = d.HookHandler(handle=lambda payload: r, tool_matcher='Bash');"
        "o = d.run_handlers({'tool_name': 'Bash'}, [h]);"
        "print(o.decision, o.reason, d.HandlerResult().additional_context == '',"
        " d.MergedHookOutcome().additional_context_fragments == [])"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "deny x True True"
