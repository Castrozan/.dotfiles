import monitor_hotplug_daemon as daemon


class TestHasExternalMonitorConnected:
    def test_true_when_external_exists(self, hyprctl_response_builder):
        hyprctl_response_builder("monitors", [{"name": "eDP-1"}, {"name": "HDMI-A-1"}])
        assert daemon.has_external_monitor_connected()

    def test_false_when_only_internal(self, hyprctl_response_builder):
        hyprctl_response_builder("monitors", [{"name": "eDP-1"}])
        assert not daemon.has_external_monitor_connected()

    def test_false_when_no_monitors(self, hyprctl_response_builder):
        hyprctl_response_builder("monitors", [])
        assert not daemon.has_external_monitor_connected()


class TestHandleMonitorRemoved:
    def test_ignores_internal_monitor_removal(self, mock_subprocess_run):
        daemon.handle_monitor_removed("eDP-1")
        batch_calls = [
            c for c in mock_subprocess_run.call_args_list if "reload" in str(c)
        ]
        assert len(batch_calls) == 0

    def test_enables_internal_on_external_removal(
        self, mock_subprocess_run, tmp_path, monkeypatch
    ):
        override = tmp_path / "override.conf"
        monkeypatch.setattr(daemon, "OVERRIDE_FILE", override)
        daemon.handle_monitor_removed("HDMI-A-1")
        assert "eDP-1" in override.read_text()


class TestHandleMonitorAdded:
    def test_ignores_internal_monitor_addition(self, mock_subprocess_run):
        daemon.handle_monitor_added("eDP-1")
        batch_calls = [
            c for c in mock_subprocess_run.call_args_list if "reload" in str(c)
        ]
        assert len(batch_calls) == 0

    def test_clears_override_on_external_addition(
        self, mock_subprocess_run, tmp_path, monkeypatch
    ):
        override = tmp_path / "override.conf"
        override.write_text("old content")
        monkeypatch.setattr(daemon, "OVERRIDE_FILE", override)
        daemon.handle_monitor_added("HDMI-A-1")
        assert override.read_text() == ""


class TestEventHandlers:
    def test_all_required_events_have_handlers(self):
        required_events = {"monitorremoved", "monitoradded"}
        assert required_events == set(daemon.EVENT_HANDLERS.keys())
