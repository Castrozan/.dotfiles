#!/usr/bin/env python3
"""E2E benchmark: wall time from `herdr tab create` until the pane's bash is writable.

Decomposes the path so the slow stage can be named. The writable phase is
measured in-band: the probe makes the pane's bash print its own `date +%s%N`
when it executes the first queued command, so client polling latency drops
out. Server phases come from the herdr server log, matched by tab id. Phase
measurement lives in herdr_bench_phases.py.

Non-invasive by construction: creates its own tabs labelled perf-bench-*,
always closes them even on failure, never focuses a window (--focus is
opt-in), reads the server log read-only, and touches no config, environment,
or shell profile. Requires a live herdr server; skips gracefully when the CLI
or server is absent.
"""

from __future__ import annotations

import argparse
import statistics
import sys

from herdr_bench_phases import herdr_cli_available, run_single_run

PHASE_METRICS = [
    "create_roundtrip",
    "server_spawn",
    "shell_visible",
    "writable",
    "prompt_visible",
    "prompt_lag_after_exec",
]


def summarize(values: list[float]) -> str:
    if not values:
        return "n/a"
    ordered = sorted(values)
    return (
        f"median={statistics.median(ordered):6.0f}  "
        f"p90={ordered[int(len(ordered) * 0.9)]:6.0f}  "
        f"min={ordered[0]:6.0f}  max={ordered[-1]:6.0f}  (n={len(ordered)})"
    )


def print_phase_header() -> None:
    print(
        f"{'run':>3}  {'create':>6}  {'srv_spawn':>9}  {'shell_vis':>9}  "
        f"{'writable':>8}  {'prompt':>7}  {'prompt_lag':>10}"
    )


def print_phase_row(run_index: int, result: dict) -> None:
    def render(metric: str) -> str:
        value = result.get(metric)
        if value is None:
            return "n/a"
        return f"{value:>9.0f}" if metric == "server_spawn" else f"{value:>7.0f}"

    print(
        f"{run_index:>3}  {render('create_roundtrip')}  {render('server_spawn')}  "
        f"{render('shell_visible')}  {render('writable')}  {render('prompt_visible')}  "
        f"{render('prompt_lag_after_exec')}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument(
        "--focus",
        action="store_true",
        help="create the tab focused instead of backgrounded",
    )
    parser.add_argument(
        "--warm",
        action="store_true",
        help="split a pane into an existing tab instead of a new tab",
    )
    args = parser.parse_args()

    if not herdr_cli_available():
        print("SKIP: no herdr server socket at ~/.config/herdr/herdr.sock")
        return 0

    print(
        f"herdr tab startup benchmark: runs={args.runs} focus={args.focus} warm_split={args.warm}"
    )
    print_phase_header()
    results: list[dict] = []
    for run_index in range(args.runs):
        result = run_single_run(run_index, args.focus, args.warm)
        if "error" in result:
            print(f"{run_index:>3}  {result['error']}")
            continue
        results.append(result)
        print_phase_row(run_index, result)

    if not results:
        print("no completed runs")
        return 1
    print()
    for metric in PHASE_METRICS:
        values = [r[metric] for r in results if r.get(metric) is not None]
        print(f"{metric:>22}: {summarize(values)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
