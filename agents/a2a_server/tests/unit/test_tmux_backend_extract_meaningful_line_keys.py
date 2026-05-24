import re

from a2a_server.backends.tmux_backend import TmuxAttachedAgentBackend


class TestExtractMeaningfulLineOccurrenceKeysInCaptureOrder:
    def test_yields_one_key_per_non_empty_line_with_occurrence_index_zero_when_unique(
        self,
    ):
        backend = TmuxAttachedAgentBackend("s", "w", meaningful_line_pattern=None)
        capture = "first line\nsecond line\nthird line\n"
        yielded = list(
            backend._extract_meaningful_line_occurrence_keys_in_capture_order(capture)
        )
        assert yielded == [("first line", 0), ("second line", 0), ("third line", 0)]

    def test_skips_blank_and_whitespace_only_lines(self):
        backend = TmuxAttachedAgentBackend("s", "w", meaningful_line_pattern=None)
        capture = "alpha\n\n   \nbeta\n\t\ngamma\n"
        yielded = list(
            backend._extract_meaningful_line_occurrence_keys_in_capture_order(capture)
        )
        assert yielded == [("alpha", 0), ("beta", 0), ("gamma", 0)]

    def test_assigns_incrementing_occurrence_indices_to_repeated_lines(self):
        backend = TmuxAttachedAgentBackend("s", "w", meaningful_line_pattern=None)
        capture = "same line\nsame line\n  same line  \nunique line\n"
        yielded = list(
            backend._extract_meaningful_line_occurrence_keys_in_capture_order(capture)
        )
        assert yielded == [
            ("same line", 0),
            ("same line", 1),
            ("same line", 2),
            ("unique line", 0),
        ]

    def test_includes_only_lines_matching_meaningful_pattern_when_set(self):
        pattern = re.compile(r"^⏺ ")
        backend = TmuxAttachedAgentBackend("s", "w", meaningful_line_pattern=pattern)
        capture = (
            "❯ user prompt\n⏺ assistant response one\n"
            "  Haiku 4.5 │ ctx 21% │ lim 19% 3h17m\n"
            "⏺ assistant response two\n✻ Cogitated for 6s\n"
        )
        yielded = list(
            backend._extract_meaningful_line_occurrence_keys_in_capture_order(capture)
        )
        assert yielded == [
            ("⏺ assistant response one", 0),
            ("⏺ assistant response two", 0),
        ]

    def test_pattern_matching_uses_normalized_stripped_form(self):
        pattern = re.compile(r"^⏺ ")
        backend = TmuxAttachedAgentBackend("s", "w", meaningful_line_pattern=pattern)
        capture = "    ⏺ leading whitespace response\n"
        yielded = list(
            backend._extract_meaningful_line_occurrence_keys_in_capture_order(capture)
        )
        assert yielded == [("⏺ leading whitespace response", 0)]

    def test_returns_empty_for_empty_capture(self):
        backend = TmuxAttachedAgentBackend("s", "w", meaningful_line_pattern=None)
        assert (
            list(backend._extract_meaningful_line_occurrence_keys_in_capture_order(""))
            == []
        )

    def test_assigns_independent_occurrence_counters_per_line_value(self):
        backend = TmuxAttachedAgentBackend("s", "w", meaningful_line_pattern=None)
        capture = "alpha\nbeta\nalpha\ngamma\nbeta\ndelta\n"
        yielded = list(
            backend._extract_meaningful_line_occurrence_keys_in_capture_order(capture)
        )
        assert yielded == [
            ("alpha", 0),
            ("beta", 0),
            ("alpha", 1),
            ("gamma", 0),
            ("beta", 1),
            ("delta", 0),
        ]
