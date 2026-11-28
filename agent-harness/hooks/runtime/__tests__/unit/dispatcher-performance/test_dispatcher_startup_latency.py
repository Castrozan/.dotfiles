import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

import pytest
from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS, find_hook_module_path

HOOKS_ROOT = Path(__file__).resolve().parents[3]

WARMUP_RUNS = 3
MEASURED_RUNS = 21
DISPATCH_OVERHEAD_BUDGET_MULTIPLIER = 1.0

READ_TOOL_PRE_TOOL_USE_PAYLOAD = {
    "session_id": "startup-latency",
    "transcript_path": "/dev/null",
    "cwd": str(HOOKS_ROOT),
    "hook_event_name": "PreToolUse",
    "tool_name": "Read",
    "tool_input": {"file_path": "/etc/hosts"},
}


def median_milliseconds_over_runs(argv, stdin_text):
    for _ in range(WARMUP_RUNS):
        subprocess.run(
            argv,
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
        )
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
        f"interpreter floor against a {budget:.1f}ms budget, so dispatching a "
        "Read now costs more than starting the interpreter it runs in. The "
        "pathlib bootstrap with eagerly imported handlers measured 1.11 floors "
        "and the current shape sits near 0.5, so overshooting here means the "
        "always-on path grew real work: a file read, a subprocess, or an "
        "eagerly imported handler the tool call could never run. "
        "test_dispatcher_import_budget.py will name what landed."
    )
