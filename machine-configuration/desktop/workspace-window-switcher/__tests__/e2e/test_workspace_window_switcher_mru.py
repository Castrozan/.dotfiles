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
    workspace_window_ids = query_aerospace_focused_workspace_window_ids()
    if len(workspace_window_ids) < 2:
        pytest.skip("focused workspace needs at least 2 windows")

    window_id_a = workspace_window_ids[0]
    window_id_b = next(
        (wid for wid in workspace_window_ids if wid != window_id_a), None
    )
    if window_id_b is None:
        pytest.skip("could not find a second distinct window")

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
        pytest.skip(f"could not establish B as focused, got {starting_focused_id}")

    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    send_command_to_daemon("commit")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS * 2)

    final_focused_id = query_aerospace_focused_window_id()
    assert final_focused_id != window_id_b, (
        f"cmd+tab stayed on B ({window_id_b}) instead of returning to the previously"
        " focused window"
    )
    assert final_focused_id == window_id_a, (
        f"focused unexpected window {final_focused_id}, expected A ({window_id_a})"
    )


def test_cancel_during_active_clears_flag_without_changing_focus():
    workspace_window_ids = query_aerospace_focused_workspace_window_ids()
    if len(workspace_window_ids) < 2:
        pytest.skip("focused workspace needs at least 2 windows")

    starting_focused_id = query_aerospace_focused_window_id()

    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    if not is_switcher_active():
        pytest.skip("switcher did not activate")

    send_command_to_daemon("cancel")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)

    assert not is_switcher_active(), "active flag still present after cancel"

    final_focused_id = query_aerospace_focused_window_id()
    assert final_focused_id == starting_focused_id, (
        f"focus changed after cancel: {starting_focused_id} -> {final_focused_id}"
    )


def test_reactivation_after_commit_starts_fresh_cycle():
    workspace_window_ids = query_aerospace_focused_workspace_window_ids()
    if len(workspace_window_ids) < 2:
        pytest.skip("focused workspace needs at least 2 windows")

    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    send_command_to_daemon("commit")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)

    assert not is_switcher_active(), "active flag still present after commit"

    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    reactivated = is_switcher_active()

    send_command_to_daemon("cancel")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)

    assert reactivated, "reactivation after commit did not set the active flag"


def test_focus_socket_message_updates_internal_mru():
    workspace_window_ids = query_aerospace_focused_workspace_window_ids()
    if len(workspace_window_ids) < 3:
        pytest.skip("focused workspace needs at least 3 windows")

    starting_focused_id = query_aerospace_focused_window_id()
    other_window_ids = [
        wid for wid in workspace_window_ids if wid != starting_focused_id
    ]
    if len(other_window_ids) < 2:
        pytest.skip("need at least two non-focused windows")

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
    assert final_focused_id == desired_second_choice_window_id, (
        f"expected the focus: socket message to make {desired_second_choice_window_id}"
        f" the next MRU pick, got {final_focused_id}"
    )
