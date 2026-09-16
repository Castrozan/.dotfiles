from .hyprland_session import (
    dispatch,
    get_clients_on_workspace,
    get_focused_address,
    spawn_kitty,
    focus_window,
    cleanup_test_workspace,
    TEST_WORKSPACE,
)
from .scenario_results import TestResult


def test_rapid_close_sequence(r: TestResult) -> None:
    print("\n--- Test: Rapid close 5 windows ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"rapid-{i}") for i in range(5)]
    for addr in addrs:
        focus_window(addr)
    for _ in range(5):
        dispatch("killactive")
    remaining = get_clients_on_workspace(TEST_WORKSPACE)
    r.check("All 5 closed", len(remaining) == 0, f"remaining: {len(remaining)}")
    cleanup_test_workspace()


def test_rapid_focus_cycle_then_close(r: TestResult) -> None:
    print("\n--- Test: Rapid focus cycling then close ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"rf-{i}") for i in range(4)]
    for _ in range(3):
        for addr in addrs:
            focus_window(addr)
    dispatch("killactive")
    r.check(
        "Rapid cycle: close 3 → 2",
        get_focused_address() == addrs[2],
        f"expected {addrs[2]}, got {get_focused_address()}",
    )
    cleanup_test_workspace()


def test_same_class_windows(r: TestResult) -> None:
    print("\n--- Test: Same class multiple windows ---")
    cleanup_test_workspace()
    addr_a = spawn_kitty("same-1")
    addr_b = spawn_kitty("same-2")
    addr_c = spawn_kitty("same-3")
    focus_window(addr_a)
    focus_window(addr_c)
    focus_window(addr_b)
    dispatch("killactive")
    r.check(
        "Same class: close same-2 → same-3",
        get_focused_address() == addr_c,
        f"expected {addr_c}, got {get_focused_address()}",
    )
    cleanup_test_workspace()


def test_ten_windows_full_chain(r: TestResult) -> None:
    print("\n--- Test: 10 window full MRU chain ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"ten-{i}") for i in range(10)]
    for addr in addrs:
        focus_window(addr)
    for i in range(9, 0, -1):
        dispatch("killactive")
        r.check(
            f"Close ten-{i} → ten-{i - 1}",
            get_focused_address() == addrs[i - 1],
            f"expected {addrs[i - 1]}, got {get_focused_address()}",
        )
    cleanup_test_workspace()
