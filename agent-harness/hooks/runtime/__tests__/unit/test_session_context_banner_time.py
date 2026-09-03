from datetime import datetime, timedelta, timezone

from session_context_banner_formatter import format_time_sections


def test_date_line_carries_zone_weekday_and_its_snapshot_nature():
    sao_paulo = timezone(timedelta(hours=-3), "-03")
    now = datetime(2026, 9, 2, 18, 6, tzinfo=sao_paulo)
    assert format_time_sections(now) == [
        "Date: 2026-09-02 18:06 -03 (Wednesday) at session start"
    ]


def test_naive_now_is_localized_instead_of_crashing():
    (date_line,) = format_time_sections(datetime(2026, 9, 2, 18, 6))
    assert date_line.startswith("Date: 2026-09-02 18:06 ")
    assert date_line.endswith("(Wednesday) at session start")
