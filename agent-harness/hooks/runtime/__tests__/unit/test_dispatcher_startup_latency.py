"""Wall-clock backstop for the hook that runs on every single tool call.

PreToolUse is registered with a `.*` matcher, so a fresh interpreter starts
for every Read, Bash, Grep and Edit an agent issues, and whatever that
interpreter does before dispatching is charged to the agent's turn.

The bound is deliberately coarse, because the ratio of dispatch cost to
interpreter cost does not survive a change of machine. Both terms are timed
here, but they are not made of the same work: the floor is mostly an already
resident interpreter binary, while dispatch is module reads, so slower
storage inflates the ratio rather than cancelling out. A first attempt at
0.65 measured 0.45 to 0.51 locally and 0.72 on CI and went red. Warming both
sides removes the bytecode-compile and cold-cache asymmetry, which is also
the honest thing to measure, since a session pays the warm cost hundreds of
times and the cold one once.

What survives is one memorable invariant: dispatching a Read must cost less
than starting the interpreter it runs in. The shape this replaced, a pathlib
bootstrap with twelve eagerly imported handlers, measured 1.11 floors. The
precise regression detector is test_dispatcher_import_budget.py, which counts
modules and is exact on any hardware; this file only catches a regression
gross enough to show up through timing noise.
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
