from unittest.mock import Mock, patch

import force_builtin_only as monitors
import monitor_configuration
import pytest
from monitor_configuration import ConnectedMonitors, DisplayMode


def test_stores_built_in_only_so_hotplug_keeps_it(monitor_state_files, monkeypatch):
    monkeypatch.setattr(
        monitors,
        "read_connected_monitors",
        lambda: ConnectedMonitors(internal="eDP-1", externals=("DP-1",)),
    )
    with (
        patch("monitor_configuration.run_hyprctl"),
        patch("monitor_configuration.migrate_workspaces_from_disabled_monitors"),
    ):
        assert monitors.force_builtin_only()
    assert monitor_configuration.read_display_mode() is DisplayMode.INTERNAL
    assert monitor_configuration.OVERRIDE_FILE.read_text() == (
        "monitor = eDP-1, preferred, auto, 1\n"
        "monitor = DP-1, disable\n"
        "monitor = , disable"
    )


def test_recenters_the_cursor_after_switching(monkeypatch):
    calls = []
    monkeypatch.setattr(monitors, "force_builtin_only", lambda: True)
    monkeypatch.setattr(
        monitors,
        "recenter_cursor_on_internal_monitor",
        lambda: calls.append("recenter"),
    )
    monkeypatch.setattr(
        monitors, "send_monitor_notification", lambda message: calls.append(message)
    )
    monitors.main()
    assert calls == ["recenter", "Built-in only"]


def test_moves_the_cursor_to_the_panel_center(monkeypatch):
    snapshot = [
        {"name": "DP-1", "width": 2560, "height": 1440},
        {"name": "eDP-1", "width": 1920, "height": 1080, "x": 100, "y": 50},
    ]
    monkeypatch.setattr(monitors, "get_all_monitors", Mock(return_value=snapshot))
    command = Mock()
    monkeypatch.setattr(monitors, "run_hyprctl", command)
    monitors.recenter_cursor_on_internal_monitor()
    command.assert_called_once_with("dispatch", "movecursor", "1060", "590")


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


def test_missing_internal_monitor_leaves_configuration_unchanged(
    monitor_state_files, monkeypatch
):
    monkeypatch.setattr(
        monitors,
        "read_connected_monitors",
        lambda: ConnectedMonitors(internal=None, externals=("DP-1",)),
    )
    notify = Mock()
    monkeypatch.setattr(monitors, "send_monitor_notification", notify)
    monitors.main()
    assert not monitor_configuration.OVERRIDE_FILE.exists()
    notify.assert_called_once_with("No internal monitor found")
