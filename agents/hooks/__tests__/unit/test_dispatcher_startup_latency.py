"""Wall-clock guard for the hook that runs on every single tool call.

PreToolUse is registered with a `.*` matcher, so a fresh interpreter starts
for every Read, Bash, Grep and Edit an agent issues, and whatever that
interpreter does before dispatching is charged to the agent's turn. The bound
is expressed against a bare interpreter measured on the same machine, so it
travels to CI hardware of any speed; what it catches is a regression in kind,
something on the always-on path that reads a file it did not need, spawns a
subprocess, or pulls a package tree in, rather than micro-drift.

Sibling to test_dispatcher_import_budget.py, which guards the same path
deterministically by module set. That one is the precise regression detector;
this one proves the saving is real in wall time.
"""

import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

import pytest
from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS, find_hook_module_path

HOOKS_ROOT = Path(__file__).resolve().parents[2]

MEASURED_RUNS = 21
DISPATCH_OVERHEAD_BUDGET_MULTIPLIER = 0.65

READ_TOOL_PRE_TOOL_USE_PAYLOAD = {
    "session_id": "startup-latency",
    "transcript_path": "/dev/null",
    "cwd": str(HOOKS_ROOT),
    "hook_event_name": "PreToolUse",
    "tool_name": "Read",
    "tool_input": {"file_path": "/etc/hosts"},
}


def median_milliseconds_over_runs(argv, stdin_text):
    durations = []
    for _ in range(MEASURED_RUNS):
        started_at = time.perf_counter()
        completed = subprocess.run(
            argv,
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
        )
        durations.append((time.perf_counter() - started_at) * 1000)
        assert completed.returncode == 0, completed.stderr
    return statistics.median(durations)


@pytest.fixture(scope="module")
def bare_interpreter_startup_milliseconds():
    return median_milliseconds_over_runs([sys.executable, "-c", "pass"], "")


@pytest.fixture(scope="module")
def pre_tool_use_dispatch_milliseconds():
    dispatcher_path = find_hook_module_path("pre-tool-use-dispatcher")
    return median_milliseconds_over_runs(
        [sys.executable, str(dispatcher_path)],
        json.dumps(READ_TOOL_PRE_TOOL_USE_PAYLOAD),
    )


def test_dispatching_a_read_costs_little_over_starting_the_interpreter(
    bare_interpreter_startup_milliseconds, pre_tool_use_dispatch_milliseconds
):
    dispatch_overhead = (
        pre_tool_use_dispatch_milliseconds - bare_interpreter_startup_milliseconds
    )
    budget = bare_interpreter_startup_milliseconds * DISPATCH_OVERHEAD_BUDGET_MULTIPLIER
    assert dispatch_overhead <= budget, (
        "everything the PreToolUse dispatcher does beyond starting the "
        "interpreter is charged to every tool call an agent makes. It measured "
        f"{dispatch_overhead:.1f}ms over a {bare_interpreter_startup_milliseconds:.1f}ms "
        f"interpreter floor against a {budget:.1f}ms budget. The bound was "
        "calibrated by measuring both shapes on one machine: the pathlib "
        "bootstrap with eagerly imported handlers came to 1.11 floors of "
        "overhead, and os.path with lazily imported handlers to 0.45, so "
        "overshooting means the always-on path grew real work again."
    )
