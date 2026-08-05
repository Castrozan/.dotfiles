#!/usr/bin/env python3

import time

import pytest

from workspace_window_switcher_helpers import (
    COMMAND_SETTLE_DELAY_SECONDS,
    PERFORMANCE_THRESHOLD_SECONDS,
    measure_command_round_trip_latency,
    move_mouse_by_offset,
    send_command_to_daemon,
)

pytestmark = pytest.mark.workspace_switcher_integration


def test_command_latency_is_acceptable():
    send_command_to_daemon("cancel")
    time.sleep(0.1)

    latencies = []
    for _ in range(10):
        latencies.append(measure_command_round_trip_latency("cancel"))
        time.sleep(0.02)

    maximum_latency = max(latencies)
    assert maximum_latency <= PERFORMANCE_THRESHOLD_SECONDS, (
        f"max socket round-trip latency {maximum_latency * 1000:.1f}ms exceeds the"
        f" {PERFORMANCE_THRESHOLD_SECONDS * 1000:.0f}ms threshold"
    )


def test_activate_deactivate_cycle_overhead_stays_within_threshold():
    cycle_times = []
    for _ in range(5):
        start_time = time.monotonic()
        send_command_to_daemon("next")
        time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
        send_command_to_daemon("cancel")
        time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
        cycle_times.append(time.monotonic() - start_time)

    average_cycle_time = sum(cycle_times) / len(cycle_times)
    overhead_per_cycle = average_cycle_time - (2 * COMMAND_SETTLE_DELAY_SECONDS)
    assert overhead_per_cycle <= PERFORMANCE_THRESHOLD_SECONDS, (
        f"activate/cancel cycle costs {overhead_per_cycle * 1000:.1f}ms beyond the"
        f" settle delays, exceeding the {PERFORMANCE_THRESHOLD_SECONDS * 1000:.0f}ms"
        " threshold"
    )


def test_mouse_movement_latency_stays_within_threshold():
    latencies = []
    for iteration in range(20):
        direction = 1 if iteration % 2 == 0 else -1
        start_time = time.monotonic()
        move_mouse_by_offset(direction * 3, direction * 3)
        latencies.append(time.monotonic() - start_time)

    maximum_latency = max(latencies)
    assert maximum_latency <= PERFORMANCE_THRESHOLD_SECONDS, (
        f"max CoreGraphics mouse-move latency {maximum_latency * 1000:.2f}ms exceeds"
        f" the {PERFORMANCE_THRESHOLD_SECONDS * 1000:.0f}ms threshold"
    )
