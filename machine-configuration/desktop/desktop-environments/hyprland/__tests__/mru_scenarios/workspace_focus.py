import time

from .hyprland_session import (
    dispatch,
    get_clients_on_workspace,
    get_focused_address,
    spawn_kitty,
    focus_window,
    cleanup_test_workspace,
    TEST_WORKSPACE,
    SETTLE_TIME,
)
from .scenario_results import TestResult


def test_single_window_close(r: TestResult) -> None:
    print("\n--- Test: Close only window ---")
    cleanup_test_workspace()
    spawn_kitty("solo")
    dispatch("killactive")
    remaining = get_clients_on_workspace(TEST_WORKSPACE)
    r.check("Only window closed", len(remaining) == 0, f"remaining: {len(remaining)}")
    cleanup_test_workspace()


def test_focus_history_survives_workspace_switch(r: TestResult) -> None:
    print("\n--- Test: MRU survives workspace switch ---")
    cleanup_test_workspace()
    addr_a = spawn_kitty("surv-A")
    addr_b = spawn_kitty("surv-B")
    focus_window(addr_a)
    focus_window(addr_b)
    dispatch("workspace", "98")
    time.sleep(SETTLE_TIME)
    dispatch("workspace", str(TEST_WORKSPACE))
    time.sleep(SETTLE_TIME)
    r.check(
        "B still focused after roundtrip",
        get_focused_address() == addr_b,
        f"expected {addr_b}, got {get_focused_address()}",
    )
    dispatch("killactive")
    r.check(
        "Close B → A (MRU preserved)",
        get_focused_address() == addr_a,
        f"expected {addr_a}, got {get_focused_address()}",
    )
    cleanup_test_workspace()
