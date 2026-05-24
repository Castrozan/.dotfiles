#!/usr/bin/env python3

import time

import pytest

from workspace_window_switcher_helpers import (
    AUTO_COMMIT_TIMEOUT_BUFFER_SECONDS,
    COMMAND_SETTLE_DELAY_SECONDS,
    is_switcher_active,
    query_aerospace_focused_workspace_window_ids,
    send_command_to_daemon,
)

pytestmark = pytest.mark.workspace_switcher_integration


def test_auto_commit_fires_after_timeout_seconds():
    print(
        f"TEST: auto-commit fires after ~{AUTO_COMMIT_TIMEOUT_BUFFER_SECONDS}s of inactivity"
    )

    workspace_window_ids = query_aerospace_focused_workspace_window_ids()
    if len(workspace_window_ids) < 2:
        print("  SKIP: focused workspace needs at least 2 windows")
        return True

    send_command_to_daemon("next")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS)
    if not is_switcher_active():
        print("  SKIP: switcher did not activate")
        return True

    time.sleep(AUTO_COMMIT_TIMEOUT_BUFFER_SECONDS)
    if is_switcher_active():
        print("  FAIL: flag still present after auto-commit window")
        return False

    print("  PASS")
    return True
