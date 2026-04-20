import datetime
import importlib.util
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "discord-agent-wrapper"
loader = importlib.machinery.SourceFileLoader("discord_agent_wrapper", str(SCRIPT_PATH))
spec = importlib.util.spec_from_loader("discord_agent_wrapper", loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestIsWithinActiveHours:
    def test_returns_true_when_no_hours_configured(self):
        assert mod.is_within_active_hours(None, None) is True

    def test_returns_true_during_active_window(self):
        with patch("time.localtime") as mock_localtime:
            mock_localtime.return_value = type("tm", (), {"tm_hour": 14})()
            assert mod.is_within_active_hours(7, 22) is True

    def test_returns_false_before_active_window(self):
        with patch("time.localtime") as mock_localtime:
            mock_localtime.return_value = type("tm", (), {"tm_hour": 3})()
            assert mod.is_within_active_hours(7, 22) is False

    def test_returns_false_after_active_window(self):
        with patch("time.localtime") as mock_localtime:
            mock_localtime.return_value = type("tm", (), {"tm_hour": 23})()
            assert mod.is_within_active_hours(7, 22) is False

    def test_returns_true_at_exact_start_hour(self):
        with patch("time.localtime") as mock_localtime:
            mock_localtime.return_value = type("tm", (), {"tm_hour": 7})()
            assert mod.is_within_active_hours(7, 22) is True

    def test_returns_false_at_exact_end_hour(self):
        with patch("time.localtime") as mock_localtime:
            mock_localtime.return_value = type("tm", (), {"tm_hour": 22})()
            assert mod.is_within_active_hours(7, 22) is False

    def test_handles_overnight_range_during_night(self):
        with patch("time.localtime") as mock_localtime:
            mock_localtime.return_value = type("tm", (), {"tm_hour": 23})()
            assert mod.is_within_active_hours(22, 7) is True

    def test_handles_overnight_range_during_day(self):
        with patch("time.localtime") as mock_localtime:
            mock_localtime.return_value = type("tm", (), {"tm_hour": 10})()
            assert mod.is_within_active_hours(22, 7) is False

    def test_handles_overnight_range_early_morning(self):
        with patch("time.localtime") as mock_localtime:
            mock_localtime.return_value = type("tm", (), {"tm_hour": 3})()
            assert mod.is_within_active_hours(22, 7) is True


class TestSecondsUntilActiveHoursStart:
    def test_same_day_future_hour(self):
        fake_now = datetime.datetime(2026, 4, 20, 3, 30, 0)
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value = fake_now
            mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(
                *args, **kw
            )
            result = mod.seconds_until_active_hours_start(7)
            assert result == 3 * 3600 + 30 * 60

    def test_next_day_when_hour_already_passed(self):
        fake_now = datetime.datetime(2026, 4, 20, 23, 0, 0)
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value = fake_now
            mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(
                *args, **kw
            )
            result = mod.seconds_until_active_hours_start(7)
            assert result == 8 * 3600


class TestShouldRotateSession:
    def test_returns_false_when_rotation_disabled(self):
        assert mod.should_rotate_session(False, "2026-04-19") is False

    def test_returns_false_when_no_previous_start(self):
        assert mod.should_rotate_session(True, None) is False

    def test_returns_false_when_same_day(self):
        with patch("time.strftime", return_value="2026-04-20"):
            assert mod.should_rotate_session(True, "2026-04-20") is False

    def test_returns_true_when_day_changed(self):
        with patch("time.strftime", return_value="2026-04-21"):
            assert mod.should_rotate_session(True, "2026-04-20") is True
