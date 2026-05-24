from unittest.mock import patch

import daily_note


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
