import pytest
from hypothesis import given
from hypothesis import strategies as st

import monitor_mode_recovery as recovery

ACER_AVAILABLE_MODES = [
    "1920x1080@60.00Hz",
    "1920x1080@164.60Hz",
    "1024x768@75.03Hz",
    "640x480@75.00Hz",
]


def acer_monitor(width, height, **fields):
    return {
        "name": "DP-1",
        "width": width,
        "height": height,
        "disabled": False,
        "availableModes": ACER_AVAILABLE_MODES,
        **fields,
    }


resolutions = st.tuples(st.integers(1, 8192), st.integers(1, 8192))


class TestMonitorRunsBelowPreferredResolution:
    @given(current=resolutions, preferred=resolutions)
    def test_degraded_exactly_when_fewer_pixels_than_the_preferred_mode(
        self, current, preferred
    ):
        monitor = {
            "width": current[0],
            "height": current[1],
            "availableModes": [f"{preferred[0]}x{preferred[1]}@60.00Hz"],
        }
        assert recovery.monitor_runs_below_preferred_resolution(monitor) is (
            current[0] * current[1] < preferred[0] * preferred[1]
        )

    @pytest.mark.parametrize(
        ("width", "height", "degraded"),
        [(1920, 1080, False), (1024, 768, True), (640, 480, True)],
    )
    def test_acer_fallback_modes_are_degraded(self, width, height, degraded):
        monitor = acer_monitor(width, height)
        assert recovery.monitor_runs_below_preferred_resolution(monitor) is degraded

    @pytest.mark.parametrize(
        "fields", [{"disabled": True}, {"availableModes": []}, {"availableModes": None}]
    )
    def test_disabled_or_modeless_monitor_is_never_degraded(self, fields):
        monitor = acer_monitor(640, 480, **fields)
        assert not recovery.monitor_runs_below_preferred_resolution(monitor)


class TestRestoreMonitorsRunningBelowPreferredResolution:
    def run_recovery(self, observed_widths):
        widths = iter(observed_widths)
        heights = {1920: 1080, 1024: 768, 640: 480}
        reloads = []
        waits = []

        def read_monitors():
            width = next(widths)
            return [acer_monitor(width, heights[width])]

        restored = recovery.restore_monitors_running_below_preferred_resolution(
            read_monitors=read_monitors,
            reload_monitors=lambda: reloads.append("reload"),
            wait_seconds=waits.append,
        )
        return restored, len(reloads), waits

    def test_healthy_monitors_are_left_alone(self):
        restored, reload_count, waits = self.run_recovery([1920])
        assert (restored, reload_count) == (True, 0)
        assert waits == [recovery.MODESET_SETTLE_SECONDS]

    def test_degraded_monitor_is_reloaded_until_it_recovers(self):
        restored, reload_count, _ = self.run_recovery([1024, 640, 1920])
        assert (restored, reload_count) == (True, 2)

    def test_gives_up_after_the_bounded_number_of_reloads(self):
        observed = [640] * (recovery.RELOAD_ATTEMPTS + 1)
        restored, reload_count, waits = self.run_recovery(observed)
        assert (restored, reload_count) == (False, recovery.RELOAD_ATTEMPTS)
        assert len(waits) == recovery.RELOAD_ATTEMPTS + 1
