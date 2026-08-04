import json
import subprocess
import sys
from pathlib import Path

import pytest
from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS, find_hook_module_path

HOOKS_ROOT = Path(__file__).resolve().parents[2]

STDLIB_MODULES_TOO_EXPENSIVE_FOR_EVERY_TOOL_CALL = {
    "dataclasses",
    "fnmatch",
    "inspect",
    "ipaddress",
    "pathlib",
    "typing",
    "urllib",
}

HANDLERS_THAT_RUN_ON_EVERY_PRE_TOOL_USE_CALL = {
    "prohibited_command_guard_handler",
    "prohibited_words_guard_handler",
}

READ_TOOL_PRE_TOOL_USE_PAYLOAD = {
    "session_id": "import-budget",
    "transcript_path": "/dev/null",
    "cwd": str(HOOKS_ROOT),
    "hook_event_name": "PreToolUse",
    "tool_name": "Read",
    "tool_input": {"file_path": "/etc/hosts"},
}


IMPORTTIME_HEADER_LABEL = "imported package"
INTERPRETER_STARTUP_MODULES = {"site", "sitecustomize"}


def modules_imported_by(dispatcher_path, payload):
    completed = subprocess.run(
        [sys.executable, "-X", "importtime", str(dispatcher_path)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    )
    assert completed.returncode == 0, completed.stderr
    imported = set()
    for line in completed.stderr.splitlines():
        if not line.startswith("import time:"):
            continue
        module_name = line.rsplit("|", 1)[-1].strip()
        if module_name != IMPORTTIME_HEADER_LABEL:
            imported.add(module_name)
    return imported


@pytest.fixture(scope="module")
def modules_a_read_tool_call_imports():
    return modules_imported_by(
        find_hook_module_path("pre-tool-use-dispatcher"), READ_TOOL_PRE_TOOL_USE_PAYLOAD
    )


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


def test_a_read_tool_call_stays_within_its_module_count_budget(
    modules_a_read_tool_call_imports,
):
    assert len(modules_a_read_tool_call_imports) <= 70, (
        "the module count is the honest proxy for hook startup cost, since every "
        "import is a stat, a read and an unmarshal in a process that lives for "
        "milliseconds; it sat at 60 when this bound was written and a jump means "
        f"a new module landed on the always-on path: {len(modules_a_read_tool_call_imports)}"
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
