from unittest.mock import Mock

import desktop_window


def client(**fields):
    return {
        "class": desktop_window.WINDOW_CLASS,
        "title": "Avatar",
        "address": "0xa",
        "floating": False,
        **fields,
    }


def fake_desktop(monkeypatch, clients):
    monitors = [
        {"focused": False},
        {
            "focused": True,
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


def test_showing_brings_a_normal_window_to_the_focused_workspace(monkeypatch):
    dispatch = fake_desktop(monkeypatch, [client()])
    desktop_window.show()
    assert [call.args for call in dispatch.call_args_list] == [
        ("movetoworkspacesilent", "4,address:0xa"),
    ]


def test_showing_tiles_a_window_left_floating(monkeypatch):
    dispatch = fake_desktop(monkeypatch, [client(floating=True)])
    desktop_window.show()
    assert ("togglefloating", "address:0xa") in [
        call.args for call in dispatch.call_args_list
    ]


def test_the_controls_window_is_never_taken_for_the_avatar(monkeypatch):
    fake_desktop(
        monkeypatch,
        [client(title=desktop_window.CONTROLS_TITLE, address="0xc"), client()],
    )
    assert desktop_window.avatar_window()["address"] == "0xa"


def test_hiding_returns_the_window_to_the_hidden_workspace(monkeypatch):
    dispatch = fake_desktop(monkeypatch, [client()])
    desktop_window.hide()
    assert [call.args for call in dispatch.call_args_list] == [
        ("movetoworkspacesilent", "special:avatar,address:0xa"),
    ]


def test_hiding_a_window_that_is_already_gone_succeeds(monkeypatch):
    dispatch = fake_desktop(monkeypatch, [])
    desktop_window.hide()
    dispatch.assert_not_called()


def test_the_desktop_is_reached_without_its_session_environment(monkeypatch):
    runner = Mock()
    monkeypatch.setattr(desktop_window.subprocess, "run", runner)
    monkeypatch.delenv("HYPRLAND_INSTANCE_SIGNATURE", raising=False)
    desktop_window.dispatch("movetoworkspacesilent", "special:avatar,address:0xa")
    assert runner.call_args.args[0][:3] == ["hyprctl", "--instance", "0"]
