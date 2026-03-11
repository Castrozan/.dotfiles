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


class TestIsUncheckedTodo:
    def test_matches_unchecked_todo(self):
        assert daily_note.is_unchecked_todo("- [ ] Buy groceries") is True

    def test_matches_with_leading_spaces(self):
        assert daily_note.is_unchecked_todo("  - [ ] Indented todo") is True

    def test_rejects_checked_todo(self):
        assert daily_note.is_unchecked_todo("- [x] Done task") is False

    def test_rejects_plain_text(self):
        assert daily_note.is_unchecked_todo("Just a line of text") is False

    def test_rejects_empty_checkbox_without_text(self):
        assert daily_note.is_unchecked_todo("- [ ]") is False


class TestIsCheckedTodo:
    def test_matches_checked_lowercase(self):
        assert daily_note.is_checked_todo("- [x] Done task") is True

    def test_matches_checked_uppercase(self):
        assert daily_note.is_checked_todo("- [X] Done task") is True

    def test_rejects_unchecked(self):
        assert daily_note.is_checked_todo("- [ ] Not done") is False


class TestNormalizeTodoContent:
    def test_strips_unchecked_prefix(self):
        assert daily_note.normalize_todo_content("- [ ] Buy milk") == "Buy milk"

    def test_strips_checked_prefix(self):
        assert daily_note.normalize_todo_content("- [x] Buy milk") == "Buy milk"

    def test_strips_whitespace(self):
        assert (
            daily_note.normalize_todo_content("  - [ ]   Extra spaces  ")
            == "Extra spaces"
        )


class TestExtractUncheckedTodosFromTodoSection:
    def test_extracts_unchecked_todos(self, tmp_path):
        note = tmp_path / "note.md"
        note.write_text(
            "# Title\n"
            "## TODO\n"
            "- [ ] Task one\n"
            "- [x] Task two\n"
            "- [ ] Task three\n"
            "## Other\n"
            "- [ ] Not in todo section\n"
        )
        result = daily_note.extract_unchecked_todos_from_todo_section(note)
        assert result == ["- [ ] Task one", "- [ ] Task three"]

    def test_returns_empty_when_no_todos(self, tmp_path):
        note = tmp_path / "note.md"
        note.write_text("# Title\n## TODO\n## Other\n")
        assert daily_note.extract_unchecked_todos_from_todo_section(note) == []

    def test_returns_empty_when_no_todo_section(self, tmp_path):
        note = tmp_path / "note.md"
        note.write_text("# Title\nSome text\n")
        assert daily_note.extract_unchecked_todos_from_todo_section(note) == []


class TestIsTodoCheckedInLaterNotes:
    def test_returns_true_when_checked_in_later_note(self, tmp_path):
        later_note = tmp_path / "daily-note" / "2026-03-09-daily-note.md"
        later_note.parent.mkdir(parents=True)
        later_note.write_text("## TODO\n- [x] Buy milk\n")

        result = daily_note.is_todo_checked_in_later_notes(
            "Buy milk", 1, ["2026-03-09", "2026-03-08"], str(tmp_path)
        )
        assert result is True

    def test_returns_false_when_not_checked(self, tmp_path):
        later_note = tmp_path / "daily-note" / "2026-03-09-daily-note.md"
        later_note.parent.mkdir(parents=True)
        later_note.write_text("## TODO\n- [ ] Buy milk\n")

        result = daily_note.is_todo_checked_in_later_notes(
            "Buy milk", 1, ["2026-03-09", "2026-03-08"], str(tmp_path)
        )
        assert result is False

    def test_returns_false_when_no_later_notes_exist(self, tmp_path):
        (tmp_path / "daily-note").mkdir(parents=True)
        result = daily_note.is_todo_checked_in_later_notes(
            "Buy milk", 0, ["2026-03-09"], str(tmp_path)
        )
        assert result is False


class TestBuildUncheckedTodosFromPastNotes:
    def test_collects_unchecked_todos_from_multiple_notes(self, tmp_path):
        daily_dir = tmp_path / "daily-note"
        daily_dir.mkdir()

        (daily_dir / "2026-03-09-daily-note.md").write_text("## TODO\n- [ ] Task A\n")
        (daily_dir / "2026-03-08-daily-note.md").write_text("## TODO\n- [ ] Task B\n")

        result = daily_note.build_unchecked_todos_from_past_notes(
            ["2026-03-09", "2026-03-08"], str(tmp_path)
        )
        assert "Task A" in result
        assert "Task B" in result

    def test_excludes_todos_checked_in_later_notes(self, tmp_path):
        daily_dir = tmp_path / "daily-note"
        daily_dir.mkdir()

        (daily_dir / "2026-03-09-daily-note.md").write_text("## TODO\n- [x] Task A\n")
        (daily_dir / "2026-03-08-daily-note.md").write_text("## TODO\n- [ ] Task A\n")

        result = daily_note.build_unchecked_todos_from_past_notes(
            ["2026-03-09", "2026-03-08"], str(tmp_path)
        )
        assert "Task A" not in result

    def test_returns_empty_when_no_notes_exist(self, tmp_path):
        (tmp_path / "daily-note").mkdir()
        result = daily_note.build_unchecked_todos_from_past_notes(
            ["2026-03-09"], str(tmp_path)
        )
        assert result == ""


class TestCreateNewDailyNote:
    def test_creates_file_with_headers(self, tmp_path):
        fullpath = tmp_path / "daily-note" / "2026-03-10-daily-note.md"

        with patch("daily_note.get_past_dates", return_value=[]):
            daily_note.create_new_daily_note(
                "2026-03-10",
                "2026-03-10-daily-note.md",
                fullpath,
                str(tmp_path),
            )

        content = fullpath.read_text()
        assert "# 2026-03-10 Daily Note" in content
        assert "## TODO" in content
        assert "## Last Daily Notes with unchecked tasks" in content

    def test_includes_unchecked_todos_from_past(self, tmp_path):
        daily_dir = tmp_path / "daily-note"
        daily_dir.mkdir()
        (daily_dir / "2026-03-09-daily-note.md").write_text(
            "## TODO\n- [ ] Pending task\n"
        )

        fullpath = daily_dir / "2026-03-10-daily-note.md"

        with patch("daily_note.get_past_dates", return_value=["2026-03-09"]):
            daily_note.create_new_daily_note(
                "2026-03-10",
                "2026-03-10-daily-note.md",
                fullpath,
                str(tmp_path),
            )

        content = fullpath.read_text()
        assert "Pending task" in content


class TestOpenDailyNoteInEditor:
    def test_opens_with_code_editor(self):
        with patch.dict("os.environ", {"EDITOR": "code"}):
            with patch("daily_note.subprocess.Popen") as mock_popen:
                daily_note.open_daily_note_in_editor("/path/to/note.md", "/vault")
                args = mock_popen.call_args[0][0]
                assert args[0] == "code"
                assert "/vault" in args
                assert "-g" in args

    def test_opens_with_vim_by_default(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("daily_note.subprocess.Popen") as mock_popen:
                daily_note.open_daily_note_in_editor("/path/to/note.md", "/vault")
                args = mock_popen.call_args[0][0]
                assert args[0] == "vim"


class TestMain:
    def test_creates_note_when_not_exists(self, tmp_path):
        with patch.dict("os.environ", {"OBSIDIAN_HOME": str(tmp_path)}):
            with patch("daily_note.open_daily_note_in_editor"):
                daily_note.main()

                daily_dir = tmp_path / "daily-note"
                notes = list(daily_dir.glob("*-daily-note.md"))
                assert len(notes) == 1

    def test_opens_existing_note_without_recreating(self, tmp_path):
        daily_dir = tmp_path / "daily-note"
        daily_dir.mkdir()

        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        existing = daily_dir / f"{today}-daily-note.md"
        existing.write_text("existing content")

        with patch.dict("os.environ", {"OBSIDIAN_HOME": str(tmp_path)}):
            with patch("daily_note.open_daily_note_in_editor"):
                daily_note.main()
                assert existing.read_text() == "existing content"
