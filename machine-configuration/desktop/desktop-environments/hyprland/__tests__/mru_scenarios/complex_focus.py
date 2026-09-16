from .hyprland_session import (
    dispatch,
    get_focused_address,
    spawn_kitty,
    focus_window,
    cleanup_test_workspace,
)
from .scenario_results import TestResult


def test_mru_interleaved_six_windows(r: TestResult) -> None:
    """Focus 0,2,4,1,3,5. Close 5→3, 3→1, 1→4."""
    print("\n--- Test: Interleaved 6-window focus ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"il-{i}") for i in range(6)]
    for idx in [0, 2, 4, 1, 3, 5]:
        focus_window(addrs[idx])
    dispatch("killactive")
    r.check(
        "Close 5 → 3",
        get_focused_address() == addrs[3],
        f"expected {addrs[3]}, got {get_focused_address()}",
    )
    dispatch("killactive")
    r.check(
        "Close 3 → 1",
        get_focused_address() == addrs[1],
        f"expected {addrs[1]}, got {get_focused_address()}",
    )
    dispatch("killactive")
    r.check(
        "Close 1 → 4",
        get_focused_address() == addrs[4],
        f"expected {addrs[4]}, got {get_focused_address()}",
    )
    cleanup_test_workspace()


def test_eight_windows_complex_pattern(r: TestResult) -> None:
    """Focus 0,3,7,2,5,1,6,4. Close 4→6, 6→1."""
    print("\n--- Test: 8 windows complex focus pattern ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"many-{i}") for i in range(8)]
    for idx in [0, 3, 7, 2, 5, 1, 6, 4]:
        focus_window(addrs[idx])
    dispatch("killactive")
    r.check(
        "Close 4 → 6 (MRU)",
        get_focused_address() == addrs[6],
        f"expected {addrs[6]}, got {get_focused_address()}",
    )
    dispatch("killactive")
    r.check(
        "Close 6 → 1",
        get_focused_address() == addrs[1],
        f"expected {addrs[1]}, got {get_focused_address()}",
    )
    cleanup_test_workspace()
