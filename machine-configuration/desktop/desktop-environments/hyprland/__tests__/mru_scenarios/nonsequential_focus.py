from .hyprland_session import (
    dispatch,
    get_focused_address,
    spawn_kitty,
    focus_window,
    cleanup_test_workspace,
)
from .scenario_results import TestResult


def test_mru_non_sequential_focus(r: TestResult) -> None:
    """A→B→C→A→C, close C → should focus A (not B)."""
    print("\n--- Test: Non-sequential focus pattern ---")
    cleanup_test_workspace()
    addr_a = spawn_kitty("ns-A")
    addr_b = spawn_kitty("ns-B")
    addr_c = spawn_kitty("ns-C")
    focus_window(addr_a)
    focus_window(addr_b)
    focus_window(addr_c)
    focus_window(addr_a)
    focus_window(addr_c)
    dispatch("killactive")
    r.check(
        "Close C → A (MRU, not B)",
        get_focused_address() == addr_a,
        f"expected {addr_a}, got {get_focused_address()}",
    )
    cleanup_test_workspace()


def test_scrolling_layout_mru_vs_spatial(r: TestResult) -> None:
    """MRU should win over spatial adjacency in scrolling layout."""
    print("\n--- Test: MRU vs spatial adjacency ---")
    cleanup_test_workspace()
    addr_a = spawn_kitty("scroll-A")
    addr_b = spawn_kitty("scroll-B")
    addr_c = spawn_kitty("scroll-C")
    focus_window(addr_a)
    focus_window(addr_c)
    dispatch("killactive")
    r.check(
        "Close C → A (MRU), not B (spatial)",
        get_focused_address() == addr_a,
        f"expected {addr_a}, got {get_focused_address()}",
    )
    cleanup_test_workspace()


def test_mru_zigzag_focus(r: TestResult) -> None:
    """A→C→B→A→C, close C → A."""
    print("\n--- Test: Zigzag focus pattern ---")
    cleanup_test_workspace()
    addr_a = spawn_kitty("zz-A")
    addr_b = spawn_kitty("zz-B")
    addr_c = spawn_kitty("zz-C")
    focus_window(addr_a)
    focus_window(addr_c)
    focus_window(addr_b)
    focus_window(addr_a)
    focus_window(addr_c)
    dispatch("killactive")
    r.check(
        "Zigzag: close C → A",
        get_focused_address() == addr_a,
        f"expected {addr_a}, got {get_focused_address()}",
    )
    cleanup_test_workspace()


def test_mru_reverse_spatial_order(r: TestResult) -> None:
    """Focus D→C→B→A (reverse spatial). Close A → B, close B → C."""
    print("\n--- Test: Reverse spatial focus order ---")
    cleanup_test_workspace()
    addr_a = spawn_kitty("rev-A")
    addr_b = spawn_kitty("rev-B")
    addr_c = spawn_kitty("rev-C")
    addr_d = spawn_kitty("rev-D")
    focus_window(addr_d)
    focus_window(addr_c)
    focus_window(addr_b)
    focus_window(addr_a)
    dispatch("killactive")
    r.check(
        "Close A → B (MRU)",
        get_focused_address() == addr_b,
        f"expected {addr_b}, got {get_focused_address()}",
    )
    dispatch("killactive")
    r.check(
        "Close B → C",
        get_focused_address() == addr_c,
        f"expected {addr_c}, got {get_focused_address()}",
    )
    cleanup_test_workspace()
