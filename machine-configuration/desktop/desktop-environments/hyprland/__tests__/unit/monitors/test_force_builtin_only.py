from unittest.mock import Mock

import force_builtin_only as monitors
import pytest


def test_monitor_classification_ignores_external_order():
    names = ["DP-1", "eDP-1", "HDMI-A-1"]
    assert monitors.find_internal_monitor_name(names) == "eDP-1"
    assert monitors.find_external_monitor_names(names) == ["DP-1", "HDMI-A-1"]
    assert monitors.find_internal_monitor_name(["DP-1"]) is None


def test_builtin_only_preserves_panel_configuration_and_migrates_before_cursor(
    monkeypatch,
):
    calls = []
    snapshot = [
        {"name": "DP-1"},
        {"name": "eDP-1", "width": 1920, "height": 1080, "x": 100, "y": 50},
    ]
    monkeypatch.setattr(monitors, "get_all_monitors", Mock(return_value=snapshot))
    monkeypatch.setattr(
        monitors,
        "find_enabled_config_line_for_monitor",
        Mock(return_value="eDP-1,1920x1080@60,0x0,1"),
    )
    for name in [
        "write_override_and_reload",
        "migrate_workspaces_from_disabled_monitors",
        "run_hyprctl",
        "send_monitor_notification",
    ]:
        monkeypatch.setattr(
            monitors,
            name,
            lambda *args, operation=name: calls.append((operation, args)),
        )
    monitors.main()
    assert calls == [
        (
            "write_override_and_reload",
            (
                "monitor = eDP-1,1920x1080@60,0x0,1\nmonitor = DP-1, disable\nmonitor = , disable\n",
            ),
        ),
        ("migrate_workspaces_from_disabled_monitors", ()),
        ("run_hyprctl", ("dispatch", "movecursor", "1060", "590")),
        ("send_monitor_notification", ("Built-in only",)),
    ]
    assert monitors.get_all_monitors.call_args_list[0].kwargs == {
        "include_disabled": True
    }
    assert monitors.get_all_monitors.call_args_list[1].kwargs == {
        "include_disabled": False
    }


@pytest.mark.parametrize(
    "snapshot",
    [[], [{"name": "DP-1"}], [{"name": "eDP-1", "width": 0, "height": 1080}]],
)
def test_cursor_does_not_move_without_usable_panel(monkeypatch, snapshot):
    monkeypatch.setattr(monitors, "get_all_monitors", Mock(return_value=snapshot))
    command = Mock()
    monkeypatch.setattr(monitors, "run_hyprctl", command)
    monitors.recenter_cursor_on_internal_monitor()
    command.assert_not_called()


def test_missing_internal_monitor_leaves_configuration_unchanged(monkeypatch):
    monkeypatch.setattr(
        monitors, "get_all_monitors", Mock(return_value=[{"name": "DP-1"}])
    )
    write, notify = Mock(), Mock()
    monkeypatch.setattr(monitors, "write_override_and_reload", write)
    monkeypatch.setattr(monitors, "send_monitor_notification", notify)
    monitors.main()
    write.assert_not_called()
    notify.assert_called_once_with("No internal monitor found")
