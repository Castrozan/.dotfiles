from unittest.mock import AsyncMock, Mock

import local_seat
import mac_seat
import mac_seat_client
import pytest


@pytest.fixture
def opened_browser(monkeypatch):
    opened = Mock()
    monkeypatch.setattr(mac_seat_client, "close_browser", Mock())
    monkeypatch.setattr(local_seat.subprocess, "run", opened)
    return opened


def seat_page_url(opened):
    return next(
        argument
        for argument in opened.call_args.args[0]
        if argument.startswith("--app=")
    )


def run_main(monkeypatch, *arguments):
    hold = AsyncMock()
    monkeypatch.setenv("AVATAR_SEAT_PAGE", "/page")
    monkeypatch.setattr(mac_seat.signal, "signal", Mock())
    monkeypatch.setattr(mac_seat, "hold_seat", hold)
    monkeypatch.setattr(mac_seat.sys, "argv", ["mac_seat.py", *arguments])
    mac_seat.main()
    return hold.call_args.args[2]


def test_a_meeting_seat_opens_one_page_in_meeting_mode(monkeypatch, opened_browser):
    run_main(monkeypatch, mac_seat_client.MEETING_FLAG)()
    assert seat_page_url(opened_browser) == "--app=http://localhost:8772/?meeting"
    assert "--headless=new" in opened_browser.call_args.args[0]
    assert opened_browser.call_count == 1


def test_a_conversation_seat_opens_the_plain_page(monkeypatch, opened_browser):
    run_main(monkeypatch)()
    assert seat_page_url(opened_browser) == "--app=http://localhost:8772/"


def test_the_meeting_page_uses_the_same_browser_profile_as_the_conversation_page(
    monkeypatch, opened_browser
):
    run_main(monkeypatch, mac_seat_client.MEETING_FLAG)()
    assert mac_seat_client.PROFILE_FLAG in opened_browser.call_args.args[0]


def test_opening_the_seat_page_first_closes_the_page_before_it(
    monkeypatch, opened_browser
):
    mac_seat.open_seat_page("?meeting")
    mac_seat_client.close_browser.assert_called_once_with()
