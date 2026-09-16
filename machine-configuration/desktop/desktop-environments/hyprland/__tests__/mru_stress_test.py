#!/usr/bin/env python3
"""
Live stress test for Hyprland MRU focus-on-close + scrolling layout.

Opens real windows on a test workspace, manipulates focus, closes them,
and verifies that focus goes to the MRU window. Requires a running Hyprland session.

Usage: python3 test_mru_stress.py
"""

import os
import sys

from mru_scenarios import (
    basic_focus,
    nonsequential_focus,
    complex_focus,
    unfocused_windows,
    rapid_operations,
    workspace_focus,
)
from mru_scenarios.hyprland_session import (
    TEST_WORKSPACE,
    hyprctl,
    get_focused_workspace_id,
    cleanup_test_workspace,
    dispatch,
)
from mru_scenarios.scenario_results import TestResult


def main() -> None:
    session = os.environ.get("XDG_SESSION_TYPE", "")
    if "wayland" not in session.lower() and not os.environ.get(
        "HYPRLAND_INSTANCE_SIGNATURE"
    ):
        print("ERROR: Not running under Hyprland")
        sys.exit(1)

    print(f"MRU Stress Test — workspace {TEST_WORKSPACE}")
    print(
        f"Hyprland: {hyprctl('version').splitlines()[0] if hyprctl('version') else '?'}"
    )
    print("=" * 60)

    original_ws = get_focused_workspace_id()
    r = TestResult()

    try:
        basic_focus.test_basic_mru_two_windows(r)
        basic_focus.test_mru_three_windows(r)
        nonsequential_focus.test_mru_non_sequential_focus(r)
        nonsequential_focus.test_scrolling_layout_mru_vs_spatial(r)
        nonsequential_focus.test_mru_zigzag_focus(r)
        basic_focus.test_mru_five_windows_chain(r)
        nonsequential_focus.test_mru_reverse_spatial_order(r)
        complex_focus.test_mru_interleaved_six_windows(r)
        complex_focus.test_eight_windows_complex_pattern(r)
        unfocused_windows.test_auto_opened_windows(r)
        unfocused_windows.test_close_unfocused_window(r)
        unfocused_windows.test_close_unfocused_then_mru_chain(r)
        unfocused_windows.test_auto_opened_close_via_address(r)
        rapid_operations.test_rapid_close_sequence(r)
        rapid_operations.test_rapid_focus_cycle_then_close(r)
        rapid_operations.test_same_class_windows(r)
        rapid_operations.test_ten_windows_full_chain(r)
        workspace_focus.test_single_window_close(r)
        workspace_focus.test_focus_history_survives_workspace_switch(r)
    finally:
        cleanup_test_workspace()
        if original_ws and original_ws > 0:
            dispatch("workspace", str(original_ws))

    success = r.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
