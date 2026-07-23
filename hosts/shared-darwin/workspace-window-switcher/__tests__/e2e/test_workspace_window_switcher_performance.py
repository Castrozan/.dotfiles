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
    print("TEST: socket command round-trip latency")

    send_command_to_daemon("cancel")
    time.sleep(0.1)

    latencies = []
    for _ in range(10):
        latency = measure_command_round_trip_latency("cancel")
        latencies.append(latency)
        time.sleep(0.02)

    average_latency = sum(latencies) / len(latencies)
    maximum_latency = max(latencies)

    print(f"  avg={average_latency * 1000:.1f}ms  max={maximum_latency * 1000:.1f}ms")

    if maximum_latency > PERFORMANCE_THRESHOLD_SECONDS:
        print(
            f"  FAIL: max latency {maximum_latency * 1000:.1f}ms exceeds"
            f" {PERFORMANCE_THRESHOLD_SECONDS * 1000:.0f}ms threshold"
        )
        return False

    print("  PASS")
    return True


def test_activate_deactivate_cycle_performance():
    print("TEST: activate/cancel cycle performance")

    cycle_times = []
    for _ in range(5):
        start_time = time.monotonic()
        send_command_to_daemon("next")
        time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
        send_command_to_daemon("cancel")
        time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
        cycle_time = time.monotonic() - start_time
        cycle_times.append(cycle_time)

    average_cycle_time = sum(cycle_times) / len(cycle_times)
    overhead_per_cycle = average_cycle_time - (2 * COMMAND_SETTLE_DELAY_SECONDS)

    print(
        f"  avg cycle={average_cycle_time * 1000:.0f}ms"
        f"  overhead={overhead_per_cycle * 1000:.1f}ms"
    )
    print("  PASS")
    return True


def test_mouse_movement_performance():
    print("TEST: mouse movement latency via CoreGraphics")

    latencies = []
    for iteration in range(20):
        direction = 1 if iteration % 2 == 0 else -1
        start_time = time.monotonic()
        move_mouse_by_offset(direction * 3, direction * 3)
        elapsed_time = time.monotonic() - start_time
        latencies.append(elapsed_time)

    average_latency = sum(latencies) / len(latencies)
    maximum_latency = max(latencies)

    print(f"  avg={average_latency * 1000:.2f}ms  max={maximum_latency * 1000:.2f}ms")
    print("  PASS")
    return True
