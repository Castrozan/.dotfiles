import time


def test_format_seconds_ago_returns_never_for_none(karabiner_status_cli_module):
    assert (
        karabiner_status_cli_module.format_seconds_ago_as_human_readable_duration(None)
        == "never"
    )


def test_format_seconds_ago_returns_seconds_under_minute(karabiner_status_cli_module):
    epoch_thirty_seconds_ago = time.time() - 30
    formatted_duration = (
        karabiner_status_cli_module.format_seconds_ago_as_human_readable_duration(
            epoch_thirty_seconds_ago
        )
    )
    assert "s ago" in formatted_duration


def test_format_seconds_ago_returns_minutes_under_hour(karabiner_status_cli_module):
    epoch_five_minutes_ago = time.time() - 300
    formatted_duration = (
        karabiner_status_cli_module.format_seconds_ago_as_human_readable_duration(
            epoch_five_minutes_ago
        )
    )
    assert "m ago" in formatted_duration


def test_format_seconds_ago_returns_hours_under_day(karabiner_status_cli_module):
    epoch_two_hours_ago = time.time() - 7200
    formatted_duration = (
        karabiner_status_cli_module.format_seconds_ago_as_human_readable_duration(
            epoch_two_hours_ago
        )
    )
    assert "h ago" in formatted_duration
