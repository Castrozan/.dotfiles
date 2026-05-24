import daily_note


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
