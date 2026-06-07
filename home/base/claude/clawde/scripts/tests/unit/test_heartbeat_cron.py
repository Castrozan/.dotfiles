import datetime
import importlib.util
import pathlib
import sys


def _load_cron_module():
    module_path = (
        pathlib.Path(__file__).resolve().parent.parent.parent / "heartbeat" / "cron.py"
    )
    module_spec = importlib.util.spec_from_file_location("heartbeat_cron", module_path)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules["heartbeat_cron"] = module
    module_spec.loader.exec_module(module)
    return module


cron_module = _load_cron_module()


def test_step_field_matches_every_fifteenth_minute():
    assert cron_module.cron_field_matches("*/15", 0, 0, 59)
    assert cron_module.cron_field_matches("*/15", 15, 0, 59)
    assert cron_module.cron_field_matches("*/15", 45, 0, 59)


def test_step_field_rejects_off_step_minute():
    assert not cron_module.cron_field_matches("*/15", 7, 0, 59)
    assert not cron_module.cron_field_matches("*/15", 14, 0, 59)


def test_comma_list_field_matches_only_listed_values():
    assert cron_module.cron_field_matches("3,33", 3, 0, 59)
    assert cron_module.cron_field_matches("3,33", 33, 0, 59)
    assert not cron_module.cron_field_matches("3,33", 4, 0, 59)
    assert not cron_module.cron_field_matches("3,33", 30, 0, 59)


def test_single_value_field_is_exact():
    assert cron_module.cron_field_matches("5", 5, 0, 59)
    assert not cron_module.cron_field_matches("5", 6, 0, 59)


def test_range_field_is_inclusive():
    assert cron_module.cron_field_matches("9-17", 9, 0, 23)
    assert cron_module.cron_field_matches("9-17", 17, 0, 23)
    assert not cron_module.cron_field_matches("9-17", 18, 0, 23)


def test_full_expression_matches_quarter_hour_any_day():
    at_quarter = datetime.datetime(2026, 6, 6, 14, 15, 0)
    off_quarter = datetime.datetime(2026, 6, 6, 14, 16, 0)
    assert cron_module.cron_expression_matches("*/15 * * * *", at_quarter)
    assert not cron_module.cron_expression_matches("*/15 * * * *", off_quarter)


def test_seconds_until_next_minute_never_exceeds_sixty():
    mid_minute = datetime.datetime(2026, 6, 6, 14, 15, 42, 500_000)
    seconds = cron_module.seconds_until_next_minute_boundary(mid_minute)
    assert 0 < seconds <= 60
