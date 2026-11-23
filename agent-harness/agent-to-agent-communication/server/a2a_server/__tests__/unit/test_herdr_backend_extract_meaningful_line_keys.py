import re

from a2a_server.backends.herdr_backend import HerdrAttachedAgentBackend


class TestExtractMeaningfulLineOccurrenceKeysInCaptureOrder:
    def test_assigns_incrementing_occurrence_indices_to_repeated_lines(self):
        backend = HerdrAttachedAgentBackend("wP:pT", meaningful_line_pattern=None)
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
        backend = HerdrAttachedAgentBackend("wP:pT", meaningful_line_pattern=pattern)
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
