from unittest.mock import patch

import daily_note


class TestGetDailyNoteFileName:
    def test_formats_filename_with_date(self):
        assert (
            daily_note.get_daily_note_file_name("2026-03-10")
            == "2026-03-10-daily-note.md"
        )

    def test_includes_suffix(self):
        result = daily_note.get_daily_note_file_name("2026-01-01")
        assert result.endswith(".md")


class TestValidateObsidianHomeIsSet:
    def test_returns_home_when_set(self):
        with patch.dict("os.environ", {"OBSIDIAN_HOME": "/home/user/vault"}):
            assert daily_note.validate_obsidian_home_is_set() == "/home/user/vault"

    def test_exits_when_not_set(self):
        with patch.dict("os.environ", {}, clear=True):
            try:
                daily_note.validate_obsidian_home_is_set()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1

    def test_exits_when_empty(self):
        with patch.dict("os.environ", {"OBSIDIAN_HOME": ""}):
            try:
                daily_note.validate_obsidian_home_is_set()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1


class TestGetPastDates:
    def test_returns_correct_number_of_dates(self):
        dates = daily_note.get_past_dates(3)
        assert len(dates) == 3

    def test_returns_dates_in_descending_order(self):
        dates = daily_note.get_past_dates(3)
        assert dates[0] > dates[1] > dates[2]

    def test_returns_empty_for_zero_days(self):
        assert daily_note.get_past_dates(0) == []
