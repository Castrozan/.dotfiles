import pytest

from chatgpt_lifecycle_policy import app_should_quit
from chatgpt_window_observer import owned_window_addresses


@pytest.mark.parametrize(
    ("window_open", "elapsed_seconds", "windowless_seconds", "expected_quit"),
    [
        (True, 90, 0, False),
        (None, 90, 90, False),
        (False, 10, 10, False),
        (False, 90, 4, False),
        (False, 30, 5, True),
        (False, 90, 60, True),
    ],
)
def test_only_a_settled_windowless_app_quits(
    window_open, elapsed_seconds, windowless_seconds, expected_quit
):
    assert (
        app_should_quit(window_open, elapsed_seconds, windowless_seconds)
        is expected_quit
    )


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
