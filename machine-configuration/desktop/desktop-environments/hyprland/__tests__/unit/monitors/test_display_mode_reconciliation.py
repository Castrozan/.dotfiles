import threading
from unittest.mock import call, patch

import monitor_configuration
from monitor_configuration import ConnectedMonitors, DisplayMode

LAPTOP_WITH_ACER = ConnectedMonitors(internal="eDP-1", externals=("DP-1",))
LAPTOP_ALONE = ConnectedMonitors(internal="eDP-1", externals=())


class TestApplyDisplayMode:
    def test_writes_the_override_reloads_and_migrates_when_it_changes(
        self, monitor_state_files
    ):
        with (
            patch("monitor_configuration.run_hyprctl") as run_hyprctl,
            patch(
                "monitor_configuration.migrate_workspaces_from_disabled_monitors"
            ) as migrate,
        ):
            changed = monitor_configuration.apply_display_mode(
                DisplayMode.EXTENDED, LAPTOP_WITH_ACER
            )

        assert changed
        assert (
            monitor_configuration.OVERRIDE_FILE.read_text()
            == "monitor = eDP-1, preferred, auto, 1"
        )
        assert run_hyprctl.call_args_list == [call("reload")]
        migrate.assert_called_once_with()

    def test_skips_the_reload_when_the_override_is_already_current(
        self, monitor_state_files
    ):
        monitor_configuration.OVERRIDE_FILE.write_text(
            "monitor = eDP-1, preferred, auto, 1"
        )
        with patch("monitor_configuration.run_hyprctl") as run_hyprctl:
            changed = monitor_configuration.apply_display_mode(
                DisplayMode.EXTENDED, LAPTOP_WITH_ACER
            )

        assert not changed
        run_hyprctl.assert_not_called()


class TestReconcileWithConnectedMonitors:
    def test_keeps_extended_through_an_external_flap_without_reloading(
        self, monitor_state_files
    ):
        monitor_configuration.write_display_mode(DisplayMode.EXTENDED)
        monitor_configuration.OVERRIDE_FILE.write_text(
            "monitor = eDP-1, preferred, auto, 1"
        )
        connection_states = iter([LAPTOP_ALONE, LAPTOP_WITH_ACER])

        with (
            patch(
                "monitor_configuration.read_connected_monitors",
                side_effect=lambda: next(connection_states),
            ),
            patch("monitor_configuration.run_hyprctl") as run_hyprctl,
            patch("monitor_configuration.migrate_workspaces_from_disabled_monitors"),
        ):
            monitor_configuration.reconcile_with_connected_monitors()
            monitor_configuration.reconcile_with_connected_monitors()

        run_hyprctl.assert_not_called()
        assert (
            monitor_configuration.OVERRIDE_FILE.read_text()
            == "monitor = eDP-1, preferred, auto, 1"
        )

    def test_restores_built_in_only_when_the_external_returns(
        self, monitor_state_files
    ):
        monitor_configuration.write_display_mode(DisplayMode.INTERNAL)
        monitor_configuration.OVERRIDE_FILE.write_text("")
        connection_states = iter([LAPTOP_ALONE, LAPTOP_WITH_ACER])
        rendered_overrides = []

        with (
            patch(
                "monitor_configuration.read_connected_monitors",
                side_effect=lambda: next(connection_states),
            ),
            patch(
                "monitor_configuration.run_hyprctl",
                side_effect=lambda *_: rendered_overrides.append(
                    monitor_configuration.OVERRIDE_FILE.read_text()
                ),
            ),
            patch("monitor_configuration.migrate_workspaces_from_disabled_monitors"),
        ):
            monitor_configuration.reconcile_with_connected_monitors()
            monitor_configuration.reconcile_with_connected_monitors()

        assert rendered_overrides == [
            "monitor = eDP-1, preferred, auto, 1",
            "monitor = eDP-1, preferred, auto, 1\n"
            "monitor = DP-1, disable\n"
            "monitor = , disable",
        ]

    def test_enables_the_panel_when_the_last_external_disconnects(
        self, monitor_state_files
    ):
        monitor_configuration.write_display_mode(DisplayMode.EXTERNAL)
        monitor_configuration.OVERRIDE_FILE.write_text("")

        with (
            patch(
                "monitor_configuration.read_connected_monitors",
                return_value=LAPTOP_ALONE,
            ),
            patch("monitor_configuration.run_hyprctl") as run_hyprctl,
            patch("monitor_configuration.migrate_workspaces_from_disabled_monitors"),
        ):
            monitor_configuration.reconcile_with_connected_monitors()

        assert (
            monitor_configuration.OVERRIDE_FILE.read_text()
            == "monitor = eDP-1, preferred, auto, 1"
        )
        assert run_hyprctl.call_args_list == [call("reload")]
        assert monitor_configuration.read_display_mode() is DisplayMode.EXTERNAL


class TestHoldReconcileLock:
    def test_serializes_concurrent_holders(self, monitor_state_files):
        first_holder_entered = threading.Event()
        release_first_holder = threading.Event()
        second_holder_entered = threading.Event()

        def first_holder() -> None:
            with monitor_configuration.hold_reconcile_lock():
                first_holder_entered.set()
                release_first_holder.wait(timeout=5)

        def second_holder() -> None:
            with monitor_configuration.hold_reconcile_lock():
                second_holder_entered.set()

        first_thread = threading.Thread(target=first_holder)
        first_thread.start()
        first_holder_entered.wait(timeout=5)
        second_thread = threading.Thread(target=second_holder)
        second_thread.start()

        assert not second_holder_entered.wait(timeout=0.2)
        release_first_holder.set()
        assert second_holder_entered.wait(timeout=5)
        first_thread.join()
        second_thread.join()
