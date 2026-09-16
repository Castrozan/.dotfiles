from unittest.mock import MagicMock, patch
import reopen_window_picker


class TestFormatEntryForDisplay:
    def test_formats_with_workspace_and_title(self):
        entry = {"workspace": 3, "title": "My Editor", "cmd": "code"}
        assert reopen_window_picker.format_entry_for_display(entry) == "[3] My Editor"

    def test_uses_defaults_for_missing_fields(self):
        entry = {"cmd": "kitty"}
        assert reopen_window_picker.format_entry_for_display(entry) == "[?] unknown"


class TestRunFuzzelPicker:
    def test_returns_selected_line(self):
        mock_result = MagicMock()
        mock_result.stdout = "[2] Browser\n"

        with patch(
            "reopen_window_picker.subprocess.run",
            return_value=mock_result,
        ) as mock_run:
            result = reopen_window_picker.run_fuzzel_picker(
                ["[1] Terminal", "[2] Browser"]
            )

            assert result == "[2] Browser"
            called_args = mock_run.call_args
            assert called_args[1]["input"] == "[2] Browser\n[1] Terminal"

    def test_returns_none_when_nothing_selected(self):
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch(
            "reopen_window_picker.subprocess.run",
            return_value=mock_result,
        ):
            result = reopen_window_picker.run_fuzzel_picker(["[1] Terminal"])
            assert result is None

    def test_returns_none_when_output_is_whitespace(self):
        mock_result = MagicMock()
        mock_result.stdout = "   \n"

        with patch(
            "reopen_window_picker.subprocess.run",
            return_value=mock_result,
        ):
            result = reopen_window_picker.run_fuzzel_picker(["[1] Terminal"])
            assert result is None
