"""Shared phase measurement for the herdr tab startup benchmark.

The benchmark drives `herdr tab create` and decomposes the wall time until the
new pane's bash is writable. This module owns the herdr CLI interaction, the
server-log phase extraction, and the per-run measurement loop; the benchmark
script owns the run schedule and the reporting.

The writable phase is in-band: the probe command makes the pane's bash print
its own `date +%s%N` at execution, so client polling latency never pollutes
it. Server phases come from the append-only herdr server log, matched by the
created tab id. Every phase is monotonic or wall-clock based but always
compared against a clock of the same origin.
"""

from __future__ import annotations

import datetime
import json
import re
import subprocess
import time
from pathlib import Path

HERDR_SOCKET_PATH = Path.home() / ".config" / "herdr" / "herdr.sock"
HERDR_SERVER_LOG_PATH = Path.home() / ".config" / "herdr" / "herdr-server.log"
TAB_LABEL_PREFIX = "perf-bench-"
PROMPT_PATTERN = re.compile(r"\$\s*$")
MARKER_PATTERN = re.compile(r"BENCH_(\d+)_(\d{16,19})")


def herdr_cli_available() -> bool:
    if not HERDR_SOCKET_PATH.exists():
        return False
    return (
        subprocess.run(["herdr", "--help"], capture_output=True, text=True).returncode
        == 0
    )


def herdr(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["herdr", *args], capture_output=True, text=True)


def parse_iso_timestamp_ns(line: str) -> int:
    match = re.match(r"(\d{4}-\d{2}-\d{2}T[\d:.]+Z)", line)
    if not match:
        raise ValueError(f"no ISO timestamp in log line: {line[:80]}")
    return int(
        datetime.datetime.fromisoformat(
            match.group(1).replace("Z", "+00:00")
        ).timestamp()
        * 1_000_000_000
    )


def read_server_log_suffix(start_offset: int) -> str:
    if not HERDR_SERVER_LOG_PATH.exists():
        return ""
    with HERDR_SERVER_LOG_PATH.open() as log_file:
        log_file.seek(start_offset)
        return log_file.read()


def extract_server_phases(log_suffix: str, tab_id: str) -> dict[str, int]:
    lines = log_suffix.splitlines()
    rename_index = next(
        (
            i
            for i, line in enumerate(lines)
            if f'tab_id="{tab_id}"' in line and "tab.rename" in line
        ),
        None,
    )
    if rename_index is None:
        return {}
    window = lines[max(0, rename_index - 20) : rename_index]
    phases: dict[str, int] = {}
    for line in window:
        if "pane.spawn.start" in line:
            phases["spawn_start"] = parse_iso_timestamp_ns(line)
        elif "pane.child_spawned" in line or "pane.spawned" in line:
            phases["child_spawned"] = parse_iso_timestamp_ns(line)
        elif 'method="tab.create"' in line and "api.request.start" in line:
            phases["request_start"] = parse_iso_timestamp_ns(line)
    return phases


def run_single_run(run_index: int, focus: bool, warm_split_into_existing: bool) -> dict:
    log_start_offset = (
        HERDR_SERVER_LOG_PATH.stat().st_size if HERDR_SERVER_LOG_PATH.exists() else 0
    )
    t0_wall_ns = time.time_ns()
    t0_mono_ns = time.monotonic_ns()

    focus_flag = ["--focus"] if focus else ["--no-focus"]
    if warm_split_into_existing:
        workspace_out = herdr(["workspace", "list"]).stdout
        try:
            workspace_id = json.loads(workspace_out)["result"][0]["id"]
        except Exception:
            workspace_id = None
        if workspace_id is None:
            return {"error": "no existing workspace to warm-split into"}
        create_output = herdr(
            [
                "pane",
                "split",
                "--pane",
                "current",
                "--direction",
                "right",
                "--cwd",
                str(Path.home()),
                *focus_flag,
            ]
        ).stdout
        pane_id = json.loads(create_output)["result"]["pane"]["id"]
        tab_id = json.loads(create_output)["result"]["pane"]["tab_id"]
    else:
        create_output = herdr(
            [
                "tab",
                "create",
                "--cwd",
                str(Path.home()),
                "--label",
                f"{TAB_LABEL_PREFIX}{run_index}",
                *focus_flag,
            ]
        ).stdout
        created = json.loads(create_output)["result"]
        pane_id = created["root_pane"]["pane_id"]
        tab_id = created["tab"]["tab_id"]

    t1_mono_ns = time.monotonic_ns()
    server_phases = extract_server_phases(
        read_server_log_suffix(log_start_offset), tab_id
    )

    run_token = f"{int(t0_wall_ns / 1_000_000_000)}"
    herdr(["pane", "run", pane_id, f"echo BENCH_{run_token}_$(/bin/date +%s%N)"])
    t_send_wall_ns = time.time_ns()

    shell_visible_mono_ns = None
    prompt_mono_ns = None
    exec_wall_ns = None
    deadline_ns = t0_mono_ns + 15_000_000_000
    while time.monotonic_ns() < deadline_ns:
        now_mono_ns = time.monotonic_ns()
        if shell_visible_mono_ns is None:
            process_info = herdr(["pane", "process-info", "--pane", pane_id]).stdout
            if '"shell_pid"' in process_info:
                shell_visible_mono_ns = now_mono_ns
        pane_output = herdr(
            ["pane", "read", pane_id, "--source", "visible", "--format", "text"]
        ).stdout
        marker_match = MARKER_PATTERN.search(pane_output)
        if marker_match and exec_wall_ns is None:
            exec_wall_ns = int(marker_match.group(2))
        if prompt_mono_ns is None and PROMPT_PATTERN.search(pane_output):
            prompt_mono_ns = now_mono_ns
        if (
            shell_visible_mono_ns is not None
            and exec_wall_ns is not None
            and prompt_mono_ns is not None
        ):
            break
        time.sleep(0.01)

    herdr(["tab", "close", tab_id])

    prompt_wall_ns = (
        t0_wall_ns + (prompt_mono_ns - t0_mono_ns) if prompt_mono_ns else None
    )
    result = {
        "create_roundtrip": (t1_mono_ns - t0_mono_ns) / 1_000_000,
        "server_spawn": None,
        "shell_visible": (shell_visible_mono_ns - t0_mono_ns) / 1_000_000
        if shell_visible_mono_ns
        else None,
        "writable": (exec_wall_ns - t_send_wall_ns) / 1_000_000
        if exec_wall_ns
        else None,
        "prompt_visible": (prompt_mono_ns - t0_mono_ns) / 1_000_000
        if prompt_mono_ns
        else None,
        "prompt_lag_after_exec": (prompt_wall_ns - exec_wall_ns) / 1_000_000
        if prompt_wall_ns and exec_wall_ns
        else None,
    }
    if server_phases.get("request_start") and server_phases.get("child_spawned"):
        result["server_spawn"] = (
            server_phases["child_spawned"] - server_phases["request_start"]
        ) / 1_000_000
    return result
