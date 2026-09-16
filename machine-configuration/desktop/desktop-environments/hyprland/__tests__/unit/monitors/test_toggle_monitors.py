from pathlib import Path
from unittest.mock import patch

import toggle_monitors


class TestDetectCurrentMode:
    def test_extended_when_both_active(self):
        result = toggle_monitors.detect_current_mode(
            ["eDP-1", "HDMI-A-1"], "eDP-1", "HDMI-A-1"
        )
        assert result == "extended"

    def test_external_when_only_external(self):
        result = toggle_monitors.detect_current_mode(["HDMI-A-1"], "eDP-1", "HDMI-A-1")
        assert result == "external"

    def test_internal_when_only_internal(self):
        result = toggle_monitors.detect_current_mode(["eDP-1"], "eDP-1", "HDMI-A-1")
        assert result == "internal"


class TestDetermineNextModeWithLidOpen:
    def test_external_to_extended(self):
        mode, label = toggle_monitors.determine_next_mode_with_lid_open("external")
        assert mode == "extended"
        assert label == "Extended"

    def test_extended_to_internal(self):
        mode, label = toggle_monitors.determine_next_mode_with_lid_open("extended")
        assert mode == "internal"
        assert label == "Built-in only"

    def test_internal_to_external(self):
        mode, label = toggle_monitors.determine_next_mode_with_lid_open("internal")
        assert mode == "external"
        assert label == "External only"


class TestDetermineNextModeWithLidClosed:
    def test_extended_to_external(self):
        mode, label = toggle_monitors.determine_next_mode_with_lid_closed("extended")
        assert mode == "external"
        assert label == "External only"

    def test_other_to_extended(self):
        mode, label = toggle_monitors.determine_next_mode_with_lid_closed("external")
        assert mode == "extended"
        assert label == "Extended"


class TestBuildOverrideContentForMode:
    def test_external_mode_is_empty(self):
        result = toggle_monitors.build_override_content_for_mode(
            "external", "eDP-1", "HDMI-A-1"
        )
        assert result == ""

    def test_internal_mode_disables_external(self):
        result = toggle_monitors.build_override_content_for_mode(
            "internal", "eDP-1", "HDMI-A-1"
        )
        assert "HDMI-A-1, disable" in result
        assert "eDP-1" in result


class TestFindInternalMonitor:
    def test_finds_edp_monitor(self):
        result = toggle_monitors.find_internal_monitor(["HDMI-A-1", "eDP-1", "DP-2"])
        assert result == "eDP-1"

    @patch.object(toggle_monitors, "MONITORS_CONF", Path("/nonexistent"))
    def test_returns_none_when_no_edp(self):
        result = toggle_monitors.find_internal_monitor(["HDMI-A-1", "DP-2"])
        assert result is None


class TestFindExternalMonitor:
    def test_finds_non_edp_monitor(self):
        result = toggle_monitors.find_external_monitor(["eDP-1", "HDMI-A-1"])
        assert result == "HDMI-A-1"

    def test_returns_none_when_only_internal(self):
        result = toggle_monitors.find_external_monitor(["eDP-1"])
        assert result is None
