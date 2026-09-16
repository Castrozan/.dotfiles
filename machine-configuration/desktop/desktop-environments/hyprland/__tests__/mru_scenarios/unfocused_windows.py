import time

from .hyprland_session import (
    hyprctl,
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


def test_auto_opened_windows(r: TestResult) -> None:
    print("\n--- Test: Auto-opened windows ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"auto-{i}") for i in range(3)]
    r.check(
        "Last spawned is focused",
        get_focused_address() == addrs[-1],
        f"expected {addrs[-1]}, got {get_focused_address()}",
    )
    dispatch("killactive")
    remaining = get_clients_on_workspace(TEST_WORKSPACE)
    r.check(
        "Focus stays on workspace",
        len(remaining) == 2
        and get_focused_address() in [c["address"] for c in remaining],
        f"focused={get_focused_address()}",
    )
    cleanup_test_workspace()


def test_close_unfocused_window(r: TestResult) -> None:
    print("\n--- Test: Close unfocused window ---")
    cleanup_test_workspace()
    addr_a = spawn_kitty("mid-A")
    addr_b = spawn_kitty("mid-B")
    addr_c = spawn_kitty("mid-C")
    focus_window(addr_a)
    focus_window(addr_b)
    focus_window(addr_c)
    hyprctl("dispatch", "closewindow", f"address:{addr_b}")
    time.sleep(SETTLE_TIME)
    r.check(
        "Closing unfocused B, C stays",
        get_focused_address() == addr_c,
        f"expected {addr_c}, got {get_focused_address()}",
    )
    cleanup_test_workspace()


def test_close_unfocused_then_mru_chain(r: TestResult) -> None:
    """Close middle of chain, then verify remaining chain."""
    print("\n--- Test: Close middle of chain ---")
    cleanup_test_workspace()
    addr_a = spawn_kitty("cm-A")
    addr_b = spawn_kitty("cm-B")
    addr_c = spawn_kitty("cm-C")
    addr_d = spawn_kitty("cm-D")
    focus_window(addr_a)
    focus_window(addr_b)
    focus_window(addr_c)
    focus_window(addr_d)
    dispatch("killactive")
    r.check(
        "Close D → C",
        get_focused_address() == addr_c,
        f"expected {addr_c}, got {get_focused_address()}",
    )
    hyprctl("dispatch", "closewindow", f"address:{addr_b}")
    time.sleep(SETTLE_TIME)
    r.check(
        "Close unfocused B, C stays",
        get_focused_address() == addr_c,
        f"expected {addr_c}, got {get_focused_address()}",
    )
    dispatch("killactive")
    r.check(
        "Close C → A (B gone)",
        get_focused_address() == addr_a,
        f"expected {addr_a}, got {get_focused_address()}",
    )
    cleanup_test_workspace()


def test_auto_opened_close_via_address(r: TestResult) -> None:
    print("\n--- Test: Auto-opened, close via address ---")
    cleanup_test_workspace()
    addr_a = spawn_kitty("nf-A")
    addr_b = spawn_kitty("nf-B")
    addr_c = spawn_kitty("nf-C")
    hyprctl("dispatch", "closewindow", f"address:{addr_a}")
    time.sleep(SETTLE_TIME)
    r.check(
        "Close A via address, C stays",
        get_focused_address() == addr_c,
        f"expected {addr_c}, got {get_focused_address()}",
    )
    dispatch("killactive")
    r.check(
        "Close C → B",
        get_focused_address() == addr_b,
        f"expected {addr_b}, got {get_focused_address()}",
    )
    cleanup_test_workspace()
