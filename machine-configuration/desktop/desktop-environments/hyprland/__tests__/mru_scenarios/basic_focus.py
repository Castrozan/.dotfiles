from .hyprland_session import (
    dispatch,
    get_focused_address,
    spawn_kitty,
    focus_window,
    cleanup_test_workspace,
)
from .scenario_results import TestResult


def test_basic_mru_two_windows(r: TestResult) -> None:
    print("\n--- Test: Basic MRU with 2 windows ---")
    cleanup_test_workspace()
    addr_a = spawn_kitty("mru-A")
    addr_b = spawn_kitty("mru-B")
    focus_window(addr_a)
    focus_window(addr_b)
    r.check(
        "B is focused",
        get_focused_address() == addr_b,
        f"expected {addr_b}, got {get_focused_address()}",
    )
    dispatch("killactive")
    r.check(
        "Close B → A (MRU)",
        get_focused_address() == addr_a,
        f"expected {addr_a}, got {get_focused_address()}",
    )
    cleanup_test_workspace()


def test_mru_three_windows(r: TestResult) -> None:
    print("\n--- Test: MRU with 3 windows ---")
    cleanup_test_workspace()
    addr_a = spawn_kitty("mru3-A")
    addr_b = spawn_kitty("mru3-B")
    addr_c = spawn_kitty("mru3-C")
    focus_window(addr_a)
    focus_window(addr_b)
    focus_window(addr_c)
    dispatch("killactive")
    r.check(
        "Close C → B",
        get_focused_address() == addr_b,
        f"expected {addr_b}, got {get_focused_address()}",
    )
    dispatch("killactive")
    r.check(
        "Close B → A",
        get_focused_address() == addr_a,
        f"expected {addr_a}, got {get_focused_address()}",
    )
    cleanup_test_workspace()


def test_mru_five_windows_chain(r: TestResult) -> None:
    print("\n--- Test: 5 window MRU chain ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"chain-{i}") for i in range(5)]
    for addr in addrs:
        focus_window(addr)
    for i in range(4, 0, -1):
        dispatch("killactive")
        r.check(
            f"Close {i} → {i - 1}",
            get_focused_address() == addrs[i - 1],
            f"expected {addrs[i - 1]}, got {get_focused_address()}",
        )
    cleanup_test_workspace()
