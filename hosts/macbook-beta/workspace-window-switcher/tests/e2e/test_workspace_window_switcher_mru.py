#!/usr/bin/env python3

import time

import pytest

from workspace_window_switcher_helpers import (
    COMMAND_SETTLE_DELAY_SECONDS,
    focus_window_via_aerospace_and_wait,
    is_switcher_active,
    query_aerospace_focused_window_id,
    query_aerospace_focused_workspace_window_ids,
    send_command_to_daemon,
)

pytestmark = pytest.mark.workspace_switcher_integration


def test_mru_picks_previously_focused_window_on_next_then_commit():
    print("TEST: cmd+tab from B selects A when A was focused before B")

    workspace_window_ids = query_aerospace_focused_workspace_window_ids()
    if len(workspace_window_ids) < 2:
        print("  SKIP: focused workspace needs at least 2 windows")
        return True

    window_id_a = workspace_window_ids[0]
    window_id_b = next(
        (wid for wid in workspace_window_ids if wid != window_id_a), None
    )
    if window_id_b is None:
        print("  SKIP: could not find a second distinct window")
        return True

    focus_window_via_aerospace_and_wait(window_id_b)

    other_workspace_window_ids = [
        wid for wid in workspace_window_ids if wid != window_id_a and wid != window_id_b
    ]
    for other_window_id in other_workspace_window_ids:
        send_command_to_daemon(f"focus:{other_window_id}")
        time.sleep(COMMAND_SETTLE_DELAY_SECONDS / 3)
    send_command_to_daemon(f"focus:{window_id_a}")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS / 3)
    send_command_to_daemon(f"focus:{window_id_b}")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS / 3)

    starting_focused_id = query_aerospace_focused_window_id()
    if starting_focused_id != window_id_b:
        print(f"  SKIP: could not establish B as focused (got {starting_focused_id})")
        return True

    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    send_command_to_daemon("commit")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS * 2)

    final_focused_id = query_aerospace_focused_window_id()
    if final_focused_id == window_id_a:
        print("  PASS")
        return True
    if final_focused_id == window_id_b:
        print(f"  FAIL: stayed on B ({window_id_b}) - the bug we fixed earlier")
        return False
    print(
        f"  FAIL: focused unexpected window {final_focused_id}, expected A ({window_id_a})"
    )
    return False


def test_cancel_during_active_clears_flag_without_changing_focus():
    print("TEST: cancel during active clears flag and preserves focus")

    workspace_window_ids = query_aerospace_focused_workspace_window_ids()
    if len(workspace_window_ids) < 2:
        print("  SKIP: focused workspace needs at least 2 windows")
        return True

    starting_focused_id = query_aerospace_focused_window_id()

    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    if not is_switcher_active():
        print("  SKIP: switcher did not activate")
        return True

    send_command_to_daemon("cancel")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)

    if is_switcher_active():
        print("  FAIL: active flag still present after cancel")
        return False

    final_focused_id = query_aerospace_focused_window_id()
    if final_focused_id != starting_focused_id:
        print(
            f"  FAIL: focus changed after cancel: {starting_focused_id} -> {final_focused_id}"
        )
        return False

    print("  PASS")
    return True


def test_reactivation_after_commit_starts_fresh_cycle():
    print("TEST: next+commit then next reactivates with fresh state")

    workspace_window_ids = query_aerospace_focused_workspace_window_ids()
    if len(workspace_window_ids) < 2:
        print("  SKIP: focused workspace needs at least 2 windows")
        return True

    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    send_command_to_daemon("commit")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)

    if is_switcher_active():
        print("  FAIL: flag still present after commit")
        return False

    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    if not is_switcher_active():
        print("  FAIL: reactivation did not set flag")
        return False

    send_command_to_daemon("cancel")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    print("  PASS")
    return True


def test_focus_socket_message_updates_internal_mru():
    print("TEST: focus:<id> socket messages influence next activation ordering")

    workspace_window_ids = query_aerospace_focused_workspace_window_ids()
    if len(workspace_window_ids) < 3:
        print("  SKIP: focused workspace needs at least 3 windows")
        return True

    starting_focused_id = query_aerospace_focused_window_id()
    other_window_ids = [
        wid for wid in workspace_window_ids if wid != starting_focused_id
    ]
    if len(other_window_ids) < 2:
        print("  SKIP: need at least two non-focused windows")
        return True

    desired_second_choice_window_id = other_window_ids[0]
    third_candidate_window_id = other_window_ids[1]

    send_command_to_daemon(f"focus:{third_candidate_window_id}")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    send_command_to_daemon(f"focus:{desired_second_choice_window_id}")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)

    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    send_command_to_daemon("commit")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS * 2)

    final_focused_id = query_aerospace_focused_window_id()
    if final_focused_id == desired_second_choice_window_id:
        print("  PASS")
        return True
    print(
        f"  FAIL: expected to land on {desired_second_choice_window_id}, "
        f"got {final_focused_id}"
    )
    return False
