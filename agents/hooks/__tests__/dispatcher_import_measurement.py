"""What a single hook invocation loads, measured the way the interpreter sees it.

Every dispatcher runs as a fresh interpreter, so its import set is its cost,
and unlike wall time that set is exactly reproducible on any machine. The
budgets are the measured counts plus a few slots of headroom: tight enough
that re-adding pathlib to a hot path, or importing a handler the matcher
cannot select, fails in a test rather than showing up as an agent that feels
slow.

Raising a budget is a deliberate act. Measure first, and if the new module is
genuinely needed on that path, move the number and say what bought it.
"""

import json
import subprocess
import sys
from pathlib import Path

from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS, find_hook_module_path

HOOKS_ROOT = Path(__file__).resolve().parent.parent

IMPORTTIME_HEADER_LABEL = "imported package"

INTERPRETER_STARTUP_MODULES = {"site", "sitecustomize"}

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

SESSION_PAYLOAD_FIELDS = {
    "session_id": "import-budget",
    "transcript_path": "/dev/null",
    "cwd": str(HOOKS_ROOT),
}

INVOCATIONS_UNDER_BUDGET = {
    "pre-tool-use/Read": (
        "pre-tool-use-dispatcher",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "/etc/hosts"},
        },
        62,
    ),
    "pre-tool-use/Bash": (
        "pre-tool-use-dispatcher",
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
        },
        73,
    ),
    "post-tool-use/Skill": (
        "post-tool-use-dispatcher",
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Skill",
            "tool_input": {},
            "tool_response": {},
        },
        75,
    ),
    "stop": (
        "stop-dispatcher",
        {"hook_event_name": "Stop", "stop_hook_active": False},
        120,
    ),
    "user-prompt-submit": (
        "user-prompt-submit-dispatcher",
        {"hook_event_name": "UserPromptSubmit", "prompt": "hello"},
        83,
    ),
}


def modules_imported_by(dispatcher_name, payload):
    completed = subprocess.run(
        [
            sys.executable,
            "-X",
            "importtime",
            str(find_hook_module_path(dispatcher_name)),
        ],
        input=json.dumps({**SESSION_PAYLOAD_FIELDS, **payload}),
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


def modules_imported_by_invocation(invocation_name):
    dispatcher_name, payload, _budget = INVOCATIONS_UNDER_BUDGET[invocation_name]
    return modules_imported_by(dispatcher_name, payload)
