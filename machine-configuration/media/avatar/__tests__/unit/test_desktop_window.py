from unittest.mock import Mock

import desktop_window
import pytest


def client(**fields):
    return {
        "class": desktop_window.WINDOW_CLASS,
        "title": "Avatar",
        "address": "0xa",
        "floating": False,
        "pinned": False,
        "at": [3176, 696],
        **fields,
    }


def fake_desktop(monkeypatch, clients):
    monkeypatch.setattr(desktop_window, "PLACEMENT_SETTLE_SECONDS", 0)
    monitors = [
        {"focused": False},
        {
            "focused": True,
            "x": 1920,
            "y": 0,
            "width": 3840,
            "height": 2160,
            "scale": 2.0,
            "activeWorkspace": {"id": 4},
        },
    ]
    monkeypatch.setattr(
        desktop_window,
        "hyprctl_json",
        lambda kind: {"clients": clients, "monitors": monitors}[kind],
    )
    dispatch = Mock()
    monkeypatch.setattr(desktop_window, "dispatch", dispatch)
    return dispatch


def test_showing_floats_the_window_in_the_corner_of_the_focused_screen(monkeypatch):
    dispatch = fake_desktop(monkeypatch, [client()])
    desktop_window.show()
    assert [call.args for call in dispatch.call_args_list] == [
        ("movetoworkspacesilent", "4,address:0xa"),
        ("togglefloating", "address:0xa"),
        ("resizewindowpixel", "exact 640 360,address:0xa"),
        ("movewindowpixel", "exact 3176 696,address:0xa"),
        ("pin", "address:0xa"),
    ]


def test_showing_twice_does_not_toggle_floating_or_pinning_off(monkeypatch):
    dispatch = fake_desktop(monkeypatch, [client(floating=True, pinned=True)])
    desktop_window.show()
    assert "togglefloating" not in [call.args[0] for call in dispatch.call_args_list]
    assert "pin" not in [call.args[0] for call in dispatch.call_args_list]


def test_placement_repeats_until_the_compositor_has_applied_it(monkeypatch):
    positions = iter([[-9999, -9999], [-9999, -9999], [10, 20]])
    dispatch = fake_desktop(monkeypatch, [])
    monkeypatch.setattr(
        desktop_window, "avatar_window", lambda: {"at": next(positions)}
    )
    desktop_window.place("address:0xa", 10, 20)
    assert dispatch.call_count == 3


def test_a_window_that_never_reaches_its_corner_fails_the_show(monkeypatch):
    fake_desktop(monkeypatch, [client(at=[-9999, -9999])])
    with pytest.raises(TimeoutError):
        desktop_window.show()


def test_the_controls_window_is_never_taken_for_the_avatar(monkeypatch):
    fake_desktop(
        monkeypatch,
        [client(title=desktop_window.CONTROLS_TITLE, address="0xc"), client()],
    )
    assert desktop_window.avatar_window()["address"] == "0xa"


def test_hiding_unpins_before_returning_to_the_hidden_workspace(monkeypatch):
    dispatch = fake_desktop(monkeypatch, [client(pinned=True)])
    desktop_window.hide()
    assert [call.args for call in dispatch.call_args_list] == [
        ("pin", "address:0xa"),
        ("movetoworkspacesilent", "special:avatar,address:0xa"),
    ]


def test_hiding_a_window_that_is_already_gone_succeeds(monkeypatch):
    dispatch = fake_desktop(monkeypatch, [])
    desktop_window.hide()
    dispatch.assert_not_called()
