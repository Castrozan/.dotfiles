import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import subprocess
import os
from zoneinfo import ZoneInfoNotFoundError

import pytest


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPECIFICATION = importlib.util.spec_from_file_location(
    "speech_policy", SCRIPTS / "speech_policy.py"
)
speech_policy = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(speech_policy)
VERIFIED_ELIGIBILITY = {
    "critical": True,
    "all_stewards_unable": True,
    "work_in_progress": False,
    "duplicate": False,
}


@pytest.fixture(autouse=True)
def forbid_external_audio_or_network(monkeypatch):
    def forbidden(*arguments, **keywords):
        raise AssertionError("Speech policy must not execute external commands")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(os, "system", forbidden)


@pytest.mark.parametrize(
    ("timestamp", "quiet"),
    [
        ("2026-10-08T08:59:59.999999-03:00", True),
        ("2026-10-08T09:00:00-03:00", False),
        ("2026-10-08T16:59:59.999999-03:00", False),
        ("2026-10-08T17:00:00-03:00", True),
        ("2026-10-08T23:59:59-03:00", True),
        ("2026-10-09T00:00:00-03:00", True),
        ("2026-10-09T08:59:59-03:00", True),
        ("2026-10-09T09:00:00-03:00", False),
        ("2026-10-08T11:59:59+00:00", True),
        ("2026-10-08T12:00:00+00:00", False),
        ("2026-10-08T19:59:59+00:00", False),
        ("2026-10-08T20:00:00+00:00", True),
        ("2026-10-09T02:00:00+09:00", False),
        ("2026-10-09T05:00:00+09:00", True),
        ("2018-12-01T18:59:59+00:00", False),
        ("2018-12-01T19:00:00+00:00", True),
    ],
)
def test_critical_alert_respects_sao_paulo_boundaries_and_timezone(timestamp, quiet):
    result = speech_policy.prepare_spoken_notification(
        "**Issue_42** needs_attention",
        now=datetime.fromisoformat(timestamp),
        **VERIFIED_ELIGIBILITY,
    )
    assert result == (None if quiet else "Issue 42 needs attention")


@pytest.mark.parametrize("day", range(7))
def test_quiet_hours_apply_every_day(day):
    beginning = datetime(2026, 10, 5, tzinfo=timezone(timedelta(hours=-3))) + timedelta(
        days=day
    )
    for hour in [0, 8, 17, 23]:
        assert (
            speech_policy.prepare_spoken_notification(
                "Critical issue",
                now=beginning.replace(hour=hour),
                **VERIFIED_ELIGIBILITY,
            )
            is None
        )


@pytest.mark.parametrize("field", VERIFIED_ELIGIBILITY)
@pytest.mark.parametrize("invalid", [None, "unknown", "false", 0, 1])
def test_unknown_or_untyped_eligibility_stays_silent(field, invalid):
    eligibility = {**VERIFIED_ELIGIBILITY, field: invalid}
    assert (
        speech_policy.prepare_spoken_notification(
            "Critical issue",
            now=datetime.fromisoformat("2026-10-08T12:00:00-03:00"),
            **eligibility,
        )
        is None
    )


@pytest.mark.parametrize("field", VERIFIED_ELIGIBILITY)
def test_each_failed_eligibility_condition_suppresses_daytime_speech(field):
    eligibility = {**VERIFIED_ELIGIBILITY, field: not VERIFIED_ELIGIBILITY[field]}
    assert (
        speech_policy.prepare_spoken_notification(
            "Critical issue",
            now=datetime.fromisoformat("2026-10-08T12:00:00-03:00"),
            **eligibility,
        )
        is None
    )


def test_missing_eligibility_stays_silent_in_daytime():
    assert (
        speech_policy.prepare_spoken_notification(
            "Critical issue", now=datetime.fromisoformat("2026-10-08T12:00:00-03:00")
        )
        is None
    )


def test_naive_clock_fails_closed():
    assert (
        speech_policy.prepare_spoken_notification(
            "Critical issue", now=datetime(2026, 10, 8, 12), **VERIFIED_ELIGIBILITY
        )
        is None
    )


def test_missing_timezone_database_fails_closed(monkeypatch):
    def unavailable(name):
        raise ZoneInfoNotFoundError(name)

    monkeypatch.setattr(speech_policy, "ZoneInfo", unavailable)
    assert (
        speech_policy.prepare_spoken_notification(
            "Critical issue",
            now=datetime.fromisoformat("2026-10-08T12:00:00-03:00"),
            **VERIFIED_ELIGIBILITY,
        )
        is None
    )


@pytest.mark.parametrize("host_timezone", ["UTC", "Pacific/Honolulu", "Asia/Tokyo"])
def test_host_timezone_does_not_change_quiet_hours(monkeypatch, host_timezone):
    monkeypatch.setenv("TZ", host_timezone)
    assert (
        speech_policy.prepare_spoken_notification(
            "Critical issue",
            now=datetime.fromisoformat("2026-10-08T20:00:00+00:00"),
            **VERIFIED_ELIGIBILITY,
        )
        is None
    )


def test_eligible_daytime_message_still_rejects_sensitive_payload():
    assert (
        speech_policy.prepare_spoken_notification(
            "API_KEY=synthetic-test-value",
            now=datetime.fromisoformat("2026-10-08T12:00:00-03:00"),
            **VERIFIED_ELIGIBILITY,
        )
        is None
    )


@pytest.mark.parametrize("hour", [8, 9, 16, 17])
def test_default_clock_uses_aware_utc_time(monkeypatch, hour):
    instant = datetime(2026, 10, 8, hour + 3, tzinfo=timezone.utc)

    class Clock:
        @staticmethod
        def now(tz):
            assert tz == timezone.utc
            return instant

    monkeypatch.setattr(speech_policy, "datetime", Clock)
    result = speech_policy.prepare_spoken_notification(
        "Issue_42", **VERIFIED_ELIGIBILITY
    )
    assert result == ("Issue 42" if 9 <= hour < 17 else None)
