import ast
import subprocess
import sys
from pathlib import Path

from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS, find_hook_module_path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
HOOK_DISPATCH_SOURCE = HOOKS_ROOT / "common" / "hook_dispatch.py"

DISPATCHER_SOURCES = [
    next(HOOKS_ROOT.rglob(dispatcher_name))
    for dispatcher_name in (
        "pre-tool-use-dispatcher.py",
        "post-tool-use-dispatcher.py",
        "stop-dispatcher.py",
        "session-start-dispatcher.py",
    )
]

MODULES_TOO_EXPENSIVE_FOR_EVERY_TOOL_CALL = {"dataclasses", "typing", "inspect"}
MODULES_TOO_EXPENSIVE_FOR_A_SYS_PATH_BOOTSTRAP = {"pathlib"}

ALWAYS_ON_PRE_TOOL_USE_HANDLER_MODULES = {
    "prohibited_command_guard_handler",
    "prohibited_command_patterns",
    "prohibited_words_guard_handler",
    "prohibited_words_segments",
}

BASH_MATCHED_PRE_TOOL_USE_HANDLER_MODULES = {
    "background_bash_anti_pattern_validator_handler",
    "workspace_directory_injector_handler",
    "worktree_location_guard_handler",
}


def module_level_imports_of(path):
    tree = ast.parse(path.read_text())
    imported = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def handler_modules_imported_at_module_level(path):
    return {
        module_name
        for module_name in module_level_imports_of(path)
        if module_name.endswith("_handler")
    }


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


def test_no_dispatcher_bootstraps_its_import_path_through_pathlib():
    offenders = {
        str(path.relative_to(HOOKS_ROOT)): sorted(
            module_level_imports_of(path)
            & MODULES_TOO_EXPENSIVE_FOR_A_SYS_PATH_BOOTSTRAP
        )
        for path in DISPATCHER_SOURCES
        if module_level_imports_of(path)
        & MODULES_TOO_EXPENSIVE_FOR_A_SYS_PATH_BOOTSTRAP
    }
    assert not offenders, (
        "every dispatcher builds sys.path before it can import anything, and pathlib "
        "drags urllib.parse, ipaddress, fnmatch and functools in for a job os.path "
        "does with modules the interpreter already loaded; measured, it cost 7ms of "
        f"the 29ms a PreToolUse invocation took. Use os.path instead: {offenders}"
    )


def test_the_always_on_pre_tool_use_handlers_avoid_pathlib():
    always_on_sources = [
        find_hook_module_path(module_name)
        for module_name in sorted(ALWAYS_ON_PRE_TOOL_USE_HANDLER_MODULES)
    ]
    offenders = {
        path.name: sorted(
            module_level_imports_of(path)
            & MODULES_TOO_EXPENSIVE_FOR_A_SYS_PATH_BOOTSTRAP
        )
        for path in always_on_sources
        if module_level_imports_of(path)
        & MODULES_TOO_EXPENSIVE_FOR_A_SYS_PATH_BOOTSTRAP
    }
    assert not offenders, (
        "these handlers carry no tool matcher, so they load on every single tool "
        "call and their imports are as hot as the dispatcher's own; keeping pathlib "
        f"out of them is what makes the lazy handler import pay off: {offenders}"
    )


def test_the_bash_matched_pre_tool_use_handlers_avoid_pathlib():
    bash_matched_sources = [
        find_hook_module_path(module_name)
        for module_name in sorted(BASH_MATCHED_PRE_TOOL_USE_HANDLER_MODULES)
    ]
    offenders = {
        path.name: sorted(
            module_level_imports_of(path)
            & MODULES_TOO_EXPENSIVE_FOR_A_SYS_PATH_BOOTSTRAP
        )
        for path in bash_matched_sources
        if module_level_imports_of(path)
        & MODULES_TOO_EXPENSIVE_FOR_A_SYS_PATH_BOOTSTRAP
    }
    assert not offenders, (
        "Bash is the tool an agent drives all day and these three load on every "
        "one of its calls, so a pathlib bootstrap here bills urllib.parse, "
        "ipaddress and math to each shell command; moving them to os.path took a "
        f"Bash invocation from 80 modules to 69: {offenders}"
    )


def test_dispatchers_defer_handler_imports_until_a_matcher_selects_one():
    offenders = {
        str(path.relative_to(HOOKS_ROOT)): sorted(
            handler_modules_imported_at_module_level(path)
        )
        for path in DISPATCHER_SOURCES
        if handler_modules_imported_at_module_level(path)
    }
    assert not offenders, (
        "a dispatcher imports every handler it can route to, but a given tool call "
        "matches at most a couple of them, so eager imports make a Read pay for the "
        "Bash, Edit, Skill and Agent handlers it will never run. Name the module in "
        f"HookHandler(handler_module_name=...) and let run_handlers import it: {offenders}"
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
