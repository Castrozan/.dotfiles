from unittest.mock import patch

import speed_read


class TestComputeOptimalRecognitionPoint:
    def test_single_char_returns_zero(self):
        assert speed_read.compute_optimal_recognition_point("a") == 0

    def test_two_char_returns_one(self):
        assert speed_read.compute_optimal_recognition_point("ab") == 1

    def test_five_char_returns_one(self):
        assert speed_read.compute_optimal_recognition_point("hello") == 1

    def test_six_char_returns_two(self):
        assert speed_read.compute_optimal_recognition_point("helloo") == 2

    def test_ten_char_returns_three(self):
        assert speed_read.compute_optimal_recognition_point("helloworld") == 3

    def test_fourteen_char_returns_formula(self):
        word = "a" * 14
        assert speed_read.compute_optimal_recognition_point(word) == (14 - 1) // 3

    def test_empty_string_returns_zero(self):
        assert speed_read.compute_optimal_recognition_point("") == 0


class TestFormatWordWithOrpHighlight:
    def test_contains_word_text(self):
        result = speed_read.format_word_with_orp_highlight("hello", 1, 40)
        assert "h" in result
        assert "llo" in result

    def test_includes_ansi_codes(self):
        result = speed_read.format_word_with_orp_highlight("test", 1, 40)
        assert "\033[" in result

    def test_single_char_word(self):
        result = speed_read.format_word_with_orp_highlight("a", 1, 40)
        assert "a" in result


class TestFormatPointerLine:
    def test_returns_pipe_with_padding(self):
        result = speed_read.format_pointer_line(40)
        assert "|" in result
        assert result.endswith("|")

    def test_padding_is_half_width(self):
        result = speed_read.format_pointer_line(40)
        assert len(result.rstrip("|")) == 20


class TestHasTrailingPunctuation:
    def test_period(self):
        assert speed_read.has_trailing_punctuation("word.") is True

    def test_exclamation(self):
        assert speed_read.has_trailing_punctuation("word!") is True

    def test_question(self):
        assert speed_read.has_trailing_punctuation("word?") is True

    def test_comma(self):
        assert speed_read.has_trailing_punctuation("word,") is True

    def test_semicolon(self):
        assert speed_read.has_trailing_punctuation("word;") is True

    def test_no_punctuation(self):
        assert speed_read.has_trailing_punctuation("word") is False

    def test_em_dash(self):
        assert speed_read.has_trailing_punctuation("word\u2014") is True


class TestStripMarkdownFormatting:
    def test_strips_bold_markers(self):
        assert speed_read.strip_markdown_formatting("**bold**") == "bold"

    def test_strips_italic_markers(self):
        assert speed_read.strip_markdown_formatting("_italic_") == "italic"

    def test_strips_backticks(self):
        assert speed_read.strip_markdown_formatting("`code`") == "code"

    def test_preserves_plain_text(self):
        assert speed_read.strip_markdown_formatting("plain") == "plain"

    def test_strips_heading_markers(self):
        assert speed_read.strip_markdown_formatting("##heading") == "heading"


class TestComputeWordDelaySeconds:
    def test_400_wpm_gives_0_15_seconds(self):
        delay = speed_read.compute_word_delay_seconds(400)
        assert abs(delay - 0.15) < 0.001

    def test_600_wpm_gives_0_1_seconds(self):
        delay = speed_read.compute_word_delay_seconds(600)
        assert abs(delay - 0.1) < 0.001

    def test_60_wpm_gives_1_second(self):
        delay = speed_read.compute_word_delay_seconds(60)
        assert abs(delay - 1.0) < 0.001


class TestParseArguments:
    def test_defaults(self):
        wpm, color, pointer, pause, file = speed_read.parse_arguments([])
        assert wpm == 400
        assert color == 1
        assert pointer is True
        assert pause is True
        assert file is None

    def test_wpm_flag(self):
        wpm, _, _, _, _ = speed_read.parse_arguments(["--wpm", "600"])
        assert wpm == 600

    def test_short_wpm_flag(self):
        wpm, _, _, _, _ = speed_read.parse_arguments(["-w", "300"])
        assert wpm == 300

    def test_color_flag(self):
        _, color, _, _, _ = speed_read.parse_arguments(["--color", "2"])
        assert color == 2

    def test_no_pointer_flag(self):
        _, _, pointer, _, _ = speed_read.parse_arguments(["--no-pointer"])
        assert pointer is False

    def test_no_pause_flag(self):
        _, _, _, pause, _ = speed_read.parse_arguments(["-P"])
        assert pause is False

    def test_input_file(self):
        _, _, _, _, file = speed_read.parse_arguments(["myfile.txt"])
        assert file == "myfile.txt"

    def test_combined_flags(self):
        wpm, color, pointer, pause, file = speed_read.parse_arguments(
            ["-w", "500", "-c", "3", "-p", "-P", "test.md"]
        )
        assert wpm == 500
        assert color == 3
        assert pointer is False
        assert pause is False
        assert file == "test.md"

    def test_help_exits_zero(self):
        try:
            speed_read.parse_arguments(["--help"])
            assert False, "Should have raised SystemExit"
        except SystemExit as e:
            assert e.code == 0

    def test_unknown_option_exits(self):
        try:
            speed_read.parse_arguments(["--bogus"])
            assert False, "Should have raised SystemExit"
        except SystemExit as e:
            assert e.code == 1

    def test_wpm_too_low_exits(self):
        try:
            speed_read.parse_arguments(["--wpm", "10"])
            assert False, "Should have raised SystemExit"
        except SystemExit as e:
            assert e.code == 1

    def test_wpm_too_high_exits(self):
        try:
            speed_read.parse_arguments(["--wpm", "3000"])
            assert False, "Should have raised SystemExit"
        except SystemExit as e:
            assert e.code == 1

    def test_env_var_wpm(self):
        with patch.dict("os.environ", {"SPEED_READ_WPM": "500"}):
            wpm, _, _, _, _ = speed_read.parse_arguments([])
            assert wpm == 500

    def test_flag_overrides_env_var(self):
        with patch.dict("os.environ", {"SPEED_READ_WPM": "500"}):
            wpm, _, _, _, _ = speed_read.parse_arguments(["--wpm", "300"])
            assert wpm == 300

    def test_env_var_pointer_false(self):
        with patch.dict("os.environ", {"SPEED_READ_POINTER": "false"}):
            _, _, pointer, _, _ = speed_read.parse_arguments([])
            assert pointer is False


class TestReadInputText:
    def test_reads_file(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        assert speed_read.read_input_text(str(test_file)) == "hello world"

    def test_exits_for_missing_file(self):
        try:
            speed_read.read_input_text("/nonexistent/file.txt")
            assert False, "Should have raised SystemExit"
        except SystemExit as e:
            assert e.code == 1

    def test_exits_when_no_input_and_tty(self):
        with patch("speed_read.sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            try:
                speed_read.read_input_text(None)
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1


class TestSplitTextIntoWords:
    def test_splits_on_whitespace(self):
        assert speed_read.split_text_into_words("hello world") == ["hello", "world"]

    def test_handles_multiple_spaces(self):
        assert speed_read.split_text_into_words("hello   world") == ["hello", "world"]

    def test_returns_empty_for_empty_string(self):
        assert speed_read.split_text_into_words("") == []

    def test_handles_newlines(self):
        assert speed_read.split_text_into_words("hello\nworld") == ["hello", "world"]


class TestMain:
    def test_exits_on_empty_words(self, tmp_path):
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("   ")

        with patch("speed_read.sys.argv", ["cmd", str(empty_file)]):
            try:
                speed_read.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1
