from datetime import datetime, timedelta, timezone

from session_context_banner_formatter import format_time_sections


def aware_now(offset_hours: float, zone_name: str) -> datetime:
    zone = timezone(timedelta(hours=offset_hours), zone_name)
    return datetime(2026, 9, 2, 18, 6, tzinfo=zone)


def test_date_line_carries_zone_weekday_and_its_snapshot_nature():
    date_line, _zone_line = format_time_sections(aware_now(-3, "-03"))
    assert date_line == "Date: 2026-09-02 18:06 -03 (Wednesday) at session start"


def test_zone_line_states_the_distance_to_utc():
    _date_line, zone_line = format_time_sections(aware_now(-3, "-03"))
    assert zone_line == "Zone: 3h behind UTC; a stamp ending in Z is UTC"


def test_half_hour_zones_ahead_of_utc_render_their_minutes():
    _date_line, zone_line = format_time_sections(aware_now(5.5, "IST"))
    assert zone_line.startswith("Zone: 5h30 ahead of UTC;")


def test_utc_itself_is_named():
    _date_line, zone_line = format_time_sections(aware_now(0, "UTC"))
    assert zone_line.startswith("Zone: UTC itself;")


def test_naive_now_is_localized_instead_of_crashing():
    date_line, zone_line = format_time_sections(datetime(2026, 9, 2, 18, 6))
    assert date_line.startswith("Date: 2026-09-02 18:06 ")
    assert zone_line.startswith("Zone: ")
