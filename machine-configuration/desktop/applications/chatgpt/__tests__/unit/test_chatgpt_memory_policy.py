import pytest

from chatgpt_memory_policy import memory_high_for_window_state
from chatgpt_window_observer import owned_window_addresses


@pytest.mark.parametrize(
    ("window_open", "elapsed_seconds", "expected_bytes"),
    [
        (True, 90, 4 * 1024**3),
        (False, 90, 1536 * 1024**2),
        (None, 90, 4 * 1024**3),
        (False, 10, 4 * 1024**3),
        (False, 30, 1536 * 1024**2),
    ],
)
def test_window_modes_preserve_startup_and_unknown_state_headroom(
    window_open, elapsed_seconds, expected_bytes
):
    assert memory_high_for_window_state(window_open, elapsed_seconds) == expected_bytes


def test_unfocused_and_off_workspace_windows_remain_open():
    clients = [
        {"pid": 42, "address": "0xabc", "mapped": True, "focusHistoryID": 7},
        {"pid": 51, "address": "0xdef", "mapped": True, "workspace": {"id": 99}},
    ]
    assert owned_window_addresses(clients, {42, 51}) == {"abc", "def"}


def test_closed_windows_and_other_applications_do_not_keep_open_mode():
    clients = [
        {"pid": 42, "address": "0xabc", "mapped": False},
        {"pid": 99, "address": "0xdef", "mapped": True, "class": "Chatgpt"},
    ]
    assert owned_window_addresses(clients, {42}) == set()


def test_one_remaining_app_window_keeps_open_mode():
    clients = [{"pid": 42, "address": "0xabc", "mapped": True}]
    assert bool(owned_window_addresses(clients, {42}))


@pytest.mark.parametrize("clients", [None, {}, "invalid", [None], [{"pid": "bad"}]])
def test_invalid_desktop_state_cannot_select_background_mode(clients):
    assert owned_window_addresses(clients, {42}) is None
