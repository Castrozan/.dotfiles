#!/usr/bin/env python3
"""
Live stress test for Hyprland MRU focus-on-close + scrolling layout.

Opens real windows on a test workspace, manipulates focus, closes them,
and verifies that focus goes to the MRU window. Requires a running Hyprland session.

Usage: python3 test_mru_stress.py
"""

import json
import os
import subprocess
import sys
import time

TEST_WORKSPACE = 99
SETTLE_TIME = 0.4
SPAWN_SETTLE = 0.6


def hyprctl(*args: str) -> str:
    result = subprocess.run(["hyprctl", *args], capture_output=True, text=True)
    return result.stdout


def hyprctl_json(*args: str) -> dict | list | None:
    output = hyprctl(*args, "-j")
    try:
        return json.loads(output) if output.strip() else None
    except json.JSONDecodeError:
        return None


def dispatch(*args: str) -> None:
    hyprctl("dispatch", *args)
    time.sleep(SETTLE_TIME)


def get_clients_on_workspace(ws_id: int) -> list[dict]:
    clients = hyprctl_json("clients") or []
    return [
        c
        for c in clients
        if c.get("workspace", {}).get("id") == ws_id and not c.get("floating", False)
    ]


def get_focused_address() -> str:
    window = hyprctl_json("activewindow")
    return window.get("address", "") if window else ""


def get_focused_workspace_id() -> int:
    window = hyprctl_json("activewindow")
    if window:
        return window.get("workspace", {}).get("id", -1)
    return -1


def spawn_kitty(title: str) -> str:
    dispatch("workspace", str(TEST_WORKSPACE))
    dispatch("exec", f"kitty --title '{title}' -e sleep 300")
    time.sleep(SPAWN_SETTLE)
    clients = get_clients_on_workspace(TEST_WORKSPACE)
    for c in clients:
        if c.get("title") == title:
            return c["address"]
    if clients:
        return sorted(clients, key=lambda c: c.get("focusHistoryID", 9999))[0][
            "address"
        ]
    return ""


def focus_window(address: str) -> None:
    dispatch("focuswindow", f"address:{address}")


def cleanup_test_workspace() -> None:
    clients = get_clients_on_workspace(TEST_WORKSPACE)
    for c in clients:
        hyprctl("dispatch", "closewindow", f"address:{c['address']}")
    time.sleep(SETTLE_TIME)
    remaining = get_clients_on_workspace(TEST_WORKSPACE)
    if remaining:
        for c in remaining:
            hyprctl("dispatch", "closewindow", f"address:{c['address']}")
        time.sleep(SETTLE_TIME)


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name: str):
        self.passed += 1
        print(f"  PASS: {name}")

    def fail(self, name: str, detail: str):
        self.failed += 1
        self.errors.append(f"{name}: {detail}")
        print(f"  FAIL: {name} — {detail}")

    def check(self, name: str, condition: bool, detail: str = ""):
        if condition:
            self.ok(name)
        else:
            self.fail(name, detail)

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Results: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print("\nFailures:")
            for e in self.errors:
                print(f"  - {e}")
        return self.failed == 0


# ── Basic MRU tests ──────────────────────────────────────────────


def test_basic_mru_two_windows(r: TestResult) -> None:
    print("\n--- Test: Basic MRU with 2 windows ---")
    cleanup_test_workspace()
    addr_a = spawn_kitty("mru-A")
    addr_b = spawn_kitty("mru-B")
    focus_window(addr_a)
    focus_window(addr_b)
    r.check("B is focused", get_focused_address() == addr_b,
            f"expected {addr_b}, got {get_focused_address()}")
    dispatch("killactive")
    r.check("Close B → A (MRU)", get_focused_address() == addr_a,
            f"expected {addr_a}, got {get_focused_address()}")
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
    r.check("Close C → B", get_focused_address() == addr_b,
            f"expected {addr_b}, got {get_focused_address()}")
    dispatch("killactive")
    r.check("Close B → A", get_focused_address() == addr_a,
            f"expected {addr_a}, got {get_focused_address()}")
    cleanup_test_workspace()


def test_mru_five_windows_chain(r: TestResult) -> None:
    print("\n--- Test: 5 window MRU chain ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"chain-{i}") for i in range(5)]
    for addr in addrs:
        focus_window(addr)
    for i in range(4, 0, -1):
        dispatch("killactive")
        r.check(f"Close {i} → {i-1}", get_focused_address() == addrs[i - 1],
                f"expected {addrs[i-1]}, got {get_focused_address()}")
    cleanup_test_workspace()


# ── Non-sequential focus (the key MRU test) ──────────────────────


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
    r.check("Close C → A (MRU, not B)", get_focused_address() == addr_a,
            f"expected {addr_a}, got {get_focused_address()}")
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
    r.check("Close C → A (MRU), not B (spatial)", get_focused_address() == addr_a,
            f"expected {addr_a}, got {get_focused_address()}")
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
    r.check("Zigzag: close C → A", get_focused_address() == addr_a,
            f"expected {addr_a}, got {get_focused_address()}")
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
    r.check("Close A → B (MRU)", get_focused_address() == addr_b,
            f"expected {addr_b}, got {get_focused_address()}")
    dispatch("killactive")
    r.check("Close B → C", get_focused_address() == addr_c,
            f"expected {addr_c}, got {get_focused_address()}")
    cleanup_test_workspace()


def test_mru_interleaved_six_windows(r: TestResult) -> None:
    """Focus 0,2,4,1,3,5. Close 5→3, 3→1, 1→4."""
    print("\n--- Test: Interleaved 6-window focus ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"il-{i}") for i in range(6)]
    for idx in [0, 2, 4, 1, 3, 5]:
        focus_window(addrs[idx])
    dispatch("killactive")
    r.check("Close 5 → 3", get_focused_address() == addrs[3],
            f"expected {addrs[3]}, got {get_focused_address()}")
    dispatch("killactive")
    r.check("Close 3 → 1", get_focused_address() == addrs[1],
            f"expected {addrs[1]}, got {get_focused_address()}")
    dispatch("killactive")
    r.check("Close 1 → 4", get_focused_address() == addrs[4],
            f"expected {addrs[4]}, got {get_focused_address()}")
    cleanup_test_workspace()


def test_eight_windows_complex_pattern(r: TestResult) -> None:
    """Focus 0,3,7,2,5,1,6,4. Close 4→6, 6→1."""
    print("\n--- Test: 8 windows complex focus pattern ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"many-{i}") for i in range(8)]
    for idx in [0, 3, 7, 2, 5, 1, 6, 4]:
        focus_window(addrs[idx])
    dispatch("killactive")
    r.check("Close 4 → 6 (MRU)", get_focused_address() == addrs[6],
            f"expected {addrs[6]}, got {get_focused_address()}")
    dispatch("killactive")
    r.check("Close 6 → 1", get_focused_address() == addrs[1],
            f"expected {addrs[1]}, got {get_focused_address()}")
    cleanup_test_workspace()


# ── Auto-opened / unfocused windows ─────────────────────────────


def test_auto_opened_windows(r: TestResult) -> None:
    print("\n--- Test: Auto-opened windows ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"auto-{i}") for i in range(3)]
    r.check("Last spawned is focused", get_focused_address() == addrs[-1],
            f"expected {addrs[-1]}, got {get_focused_address()}")
    dispatch("killactive")
    remaining = get_clients_on_workspace(TEST_WORKSPACE)
    r.check("Focus stays on workspace", len(remaining) == 2
            and get_focused_address() in [c["address"] for c in remaining],
            f"focused={get_focused_address()}")
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
    r.check("Closing unfocused B, C stays", get_focused_address() == addr_c,
            f"expected {addr_c}, got {get_focused_address()}")
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
    r.check("Close D → C", get_focused_address() == addr_c,
            f"expected {addr_c}, got {get_focused_address()}")
    hyprctl("dispatch", "closewindow", f"address:{addr_b}")
    time.sleep(SETTLE_TIME)
    r.check("Close unfocused B, C stays", get_focused_address() == addr_c,
            f"expected {addr_c}, got {get_focused_address()}")
    dispatch("killactive")
    r.check("Close C → A (B gone)", get_focused_address() == addr_a,
            f"expected {addr_a}, got {get_focused_address()}")
    cleanup_test_workspace()


def test_auto_opened_close_via_address(r: TestResult) -> None:
    print("\n--- Test: Auto-opened, close via address ---")
    cleanup_test_workspace()
    addr_a = spawn_kitty("nf-A")
    addr_b = spawn_kitty("nf-B")
    addr_c = spawn_kitty("nf-C")
    hyprctl("dispatch", "closewindow", f"address:{addr_a}")
    time.sleep(SETTLE_TIME)
    r.check("Close A via address, C stays", get_focused_address() == addr_c,
            f"expected {addr_c}, got {get_focused_address()}")
    dispatch("killactive")
    r.check("Close C → B", get_focused_address() == addr_b,
            f"expected {addr_b}, got {get_focused_address()}")
    cleanup_test_workspace()


# ── Stress tests ─────────────────────────────────────────────────


def test_rapid_close_sequence(r: TestResult) -> None:
    print("\n--- Test: Rapid close 5 windows ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"rapid-{i}") for i in range(5)]
    for addr in addrs:
        focus_window(addr)
    for _ in range(5):
        dispatch("killactive")
    remaining = get_clients_on_workspace(TEST_WORKSPACE)
    r.check("All 5 closed", len(remaining) == 0,
            f"remaining: {len(remaining)}")
    cleanup_test_workspace()


def test_rapid_focus_cycle_then_close(r: TestResult) -> None:
    print("\n--- Test: Rapid focus cycling then close ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"rf-{i}") for i in range(4)]
    for _ in range(3):
        for addr in addrs:
            focus_window(addr)
    dispatch("killactive")
    r.check("Rapid cycle: close 3 → 2", get_focused_address() == addrs[2],
            f"expected {addrs[2]}, got {get_focused_address()}")
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
    r.check("Same class: close same-2 → same-3", get_focused_address() == addr_c,
            f"expected {addr_c}, got {get_focused_address()}")
    cleanup_test_workspace()


def test_ten_windows_full_chain(r: TestResult) -> None:
    print("\n--- Test: 10 window full MRU chain ---")
    cleanup_test_workspace()
    addrs = [spawn_kitty(f"ten-{i}") for i in range(10)]
    for addr in addrs:
        focus_window(addr)
    for i in range(9, 0, -1):
        dispatch("killactive")
        r.check(f"Close ten-{i} → ten-{i-1}",
                get_focused_address() == addrs[i - 1],
                f"expected {addrs[i-1]}, got {get_focused_address()}")
    cleanup_test_workspace()


# ── Workspace / single window edge cases ─────────────────────────


def test_single_window_close(r: TestResult) -> None:
    print("\n--- Test: Close only window ---")
    cleanup_test_workspace()
    spawn_kitty("solo")
    dispatch("killactive")
    remaining = get_clients_on_workspace(TEST_WORKSPACE)
    r.check("Only window closed", len(remaining) == 0,
            f"remaining: {len(remaining)}")
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
    r.check("B still focused after roundtrip", get_focused_address() == addr_b,
            f"expected {addr_b}, got {get_focused_address()}")
    dispatch("killactive")
    r.check("Close B → A (MRU preserved)", get_focused_address() == addr_a,
            f"expected {addr_a}, got {get_focused_address()}")
    cleanup_test_workspace()


# ── Main ─────────────────────────────────────────────────────────


def main() -> None:
    session = os.environ.get("XDG_SESSION_TYPE", "")
    if "wayland" not in session.lower() and not os.environ.get(
        "HYPRLAND_INSTANCE_SIGNATURE"
    ):
        print("ERROR: Not running under Hyprland")
        sys.exit(1)

    print(f"MRU Stress Test — workspace {TEST_WORKSPACE}")
    print(f"Hyprland: {hyprctl('version').splitlines()[0] if hyprctl('version') else '?'}")
    print("=" * 60)

    original_ws = get_focused_workspace_id()
    r = TestResult()

    try:
        test_basic_mru_two_windows(r)
        test_mru_three_windows(r)
        test_mru_non_sequential_focus(r)
        test_scrolling_layout_mru_vs_spatial(r)
        test_mru_zigzag_focus(r)
        test_mru_five_windows_chain(r)
        test_mru_reverse_spatial_order(r)
        test_mru_interleaved_six_windows(r)
        test_eight_windows_complex_pattern(r)
        test_auto_opened_windows(r)
        test_close_unfocused_window(r)
        test_close_unfocused_then_mru_chain(r)
        test_auto_opened_close_via_address(r)
        test_rapid_close_sequence(r)
        test_rapid_focus_cycle_then_close(r)
        test_same_class_windows(r)
        test_ten_windows_full_chain(r)
        test_single_window_close(r)
        test_focus_history_survives_workspace_switch(r)
    finally:
        cleanup_test_workspace()
        if original_ws and original_ws > 0:
            dispatch("workspace", str(original_ws))

    success = r.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
