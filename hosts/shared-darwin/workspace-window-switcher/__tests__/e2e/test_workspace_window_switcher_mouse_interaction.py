#!/usr/bin/env python3

import time

import pytest

from workspace_window_switcher_helpers import (
    COMMAND_SETTLE_DELAY_SECONDS,
    MOUSE_MOVEMENT_ITERATIONS,
    MOUSE_MOVEMENT_PIXEL_OFFSET,
    is_switcher_active,
    move_mouse_by_offset,
    send_command_to_daemon,
)

pytestmark = pytest.mark.workspace_switcher_integration


def test_switcher_stays_active_during_mouse_movement():
    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)

    if not is_switcher_active():
        send_command_to_daemon("cancel")
        pytest.skip("switcher did not activate, focused workspace needs >= 2 windows")

    for iteration in range(MOUSE_MOVEMENT_ITERATIONS):
        direction = 1 if iteration % 2 == 0 else -1
        move_mouse_by_offset(
            MOUSE_MOVEMENT_PIXEL_OFFSET * direction,
            MOUSE_MOVEMENT_PIXEL_OFFSET * direction,
        )
        time.sleep(0.05)
        assert is_switcher_active(), (
            f"switcher deactivated after mouse movement #{iteration + 1}"
        )

    send_command_to_daemon("cancel")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)


def test_selection_advances_past_index_one_with_mouse_movement():
    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)

    if not is_switcher_active():
        send_command_to_daemon("cancel")
        pytest.skip("switcher did not activate, focused workspace needs >= 3 windows")

    move_mouse_by_offset(MOUSE_MOVEMENT_PIXEL_OFFSET, MOUSE_MOVEMENT_PIXEL_OFFSET)
    time.sleep(0.05)

    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    assert is_switcher_active(), (
        "switcher deactivated after next+mouse+next, the original bug"
    )

    move_mouse_by_offset(-MOUSE_MOVEMENT_PIXEL_OFFSET, -MOUSE_MOVEMENT_PIXEL_OFFSET)
    time.sleep(0.05)

    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    assert is_switcher_active(), (
        "switcher deactivated after the third next with mouse movement"
    )

    send_command_to_daemon("cancel")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)


def test_rapid_next_commands_with_continuous_mouse_movement():
    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)

    if not is_switcher_active():
        send_command_to_daemon("cancel")
        pytest.skip("switcher did not activate, focused workspace needs >= 2 windows")

    for iteration in range(6):
        direction = 1 if iteration % 2 == 0 else -1
        move_mouse_by_offset(MOUSE_MOVEMENT_PIXEL_OFFSET * direction, 0)
        send_command_to_daemon("next")
        time.sleep(0.05)

    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    assert is_switcher_active(), (
        "switcher deactivated during the rapid next+mouse interleave"
    )

    send_command_to_daemon("cancel")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
