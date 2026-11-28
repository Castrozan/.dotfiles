import time

import pytest


def test_format_seconds_ago_returns_never_for_none(karabiner_status_cli_module):
    assert (
        karabiner_status_cli_module.format_seconds_ago_as_human_readable_duration(None)
        == "never"
    )


@pytest.mark.parametrize(
    ("seconds_elapsed", "expected_unit"), [(30, "s ago"), (300, "m ago")]
)
def test_format_seconds_ago_picks_the_largest_unit_that_fits(
    karabiner_status_cli_module, seconds_elapsed, expected_unit
):
    formatted_duration = (
        karabiner_status_cli_module.format_seconds_ago_as_human_readable_duration(
            time.time() - seconds_elapsed
        )
    )
    assert expected_unit in formatted_duration


def test_format_seconds_ago_returns_hours_under_day(karabiner_status_cli_module):
    epoch_two_hours_ago = time.time() - 7200
    formatted_duration = (
        karabiner_status_cli_module.format_seconds_ago_as_human_readable_duration(
            epoch_two_hours_ago
        )
    )
    assert "h ago" in formatted_duration
