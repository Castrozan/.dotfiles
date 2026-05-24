import daily_note


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
