"""What must never appear on a hot hook path, whatever the count says.

A budget catches drift in aggregate. These catch the specific mistakes that
made the budget necessary: a pathlib bootstrap dragging three modules behind
it, a handler imported before its matcher could select it, and a third-party
import that ties the hooks to an environment rather than the bare interpreter
run-hook.sh pins.

Read and Bash are both checked because they cost differently. A Read selects
only the two matcher-less guards; a Bash selects four more, and Bash is the
tool an agent drives all day.
"""

import sys

import pytest
from dispatcher_import_measurement import (
    HANDLERS_THAT_RUN_ON_EVERY_PRE_TOOL_USE_CALL,
    HOOKS_ROOT,
    INTERPRETER_STARTUP_MODULES,
    STDLIB_MODULES_TOO_EXPENSIVE_FOR_EVERY_TOOL_CALL,
    modules_imported_by_invocation,
)


@pytest.fixture(scope="module")
def modules_a_read_tool_call_imports():
    return modules_imported_by_invocation("pre-tool-use/Read")


@pytest.fixture(scope="module")
def modules_a_bash_tool_call_imports():
    return modules_imported_by_invocation("pre-tool-use/Bash")


def test_a_read_tool_call_skips_the_expensive_stdlib_modules(
    modules_a_read_tool_call_imports,
):
    offenders = sorted(
        modules_a_read_tool_call_imports
        & STDLIB_MODULES_TOO_EXPENSIVE_FOR_EVERY_TOOL_CALL
    )
    assert not offenders, (
        "PreToolUse is registered for every tool, so a plain Read spawns this "
        "interpreter and pays for whatever it imports; pathlib alone drags in "
        "urllib.parse, ipaddress and fnmatch and cost 7ms of a 29ms invocation. "
        f"Bootstrap sys.path with os.path instead: {offenders}"
    )


def test_a_bash_tool_call_skips_the_expensive_stdlib_modules(
    modules_a_bash_tool_call_imports,
):
    offenders = sorted(
        modules_a_bash_tool_call_imports
        & STDLIB_MODULES_TOO_EXPENSIVE_FOR_EVERY_TOOL_CALL
    )
    assert not offenders, (
        "a Bash call selects four more guards than a Read does, so one pathlib "
        "bootstrap among them charges urllib.parse, ipaddress and math to every "
        "shell command the agent runs; that cost 9ms of every Bash call until the "
        f"three Bash-matched handlers moved to os.path: {offenders}"
    )


def test_a_read_tool_call_imports_no_handler_it_cannot_run(
    modules_a_read_tool_call_imports,
):
    imported_handlers = {
        module_name
        for module_name in modules_a_read_tool_call_imports
        if module_name.endswith("_handler")
    }
    offenders = sorted(imported_handlers - HANDLERS_THAT_RUN_ON_EVERY_PRE_TOOL_USE_CALL)
    assert not offenders, (
        "only the two matcher-less guards can run on a Read, so every other "
        "handler imported here is dead weight the tool call paid for. Keep the "
        "handler table on HookHandler(handler_module_name=...) so run_handlers "
        f"imports a handler only once its matcher selects it: {offenders}"
    )


def test_the_hooks_import_nothing_outside_the_standard_library(
    modules_a_read_tool_call_imports,
):
    hook_module_names = {
        source_path.stem
        for source_path in HOOKS_ROOT.rglob("*.py")
        if "__pycache__" not in source_path.parts
    }
    third_party = sorted(
        module_name
        for module_name in modules_a_read_tool_call_imports
        if module_name.split(".")[0] not in sys.stdlib_module_names
        and module_name.split(".")[0] not in hook_module_names
        and module_name not in INTERPRETER_STARTUP_MODULES
        and not module_name.startswith("_")
    )
    assert not third_party, (
        "a third-party import costs a package directory walk on top of its own "
        "load, in a process that has milliseconds to live and runs on every tool "
        "call; it also ties the hooks to a python environment rather than the "
        f"bare interpreter run-hook.sh pins: {third_party}"
    )
