from evaluation_assertion_policy.negative_regex import (
    bare_token_expressions_in_regex,
)


def test_bare_token_regex_detection_rejects_keyword_only_alternatives():
    for pattern in (
        "TODO",
        r"\bTODO\b",
        "TODO|FIXME",
        r"\b(?:TODO|FIXME)\b",
        r"#\s|\b(?:TODO|FIXME)\b",
    ):
        assert bare_token_expressions_in_regex(pattern)


def test_bare_token_regex_detection_preserves_structural_patterns():
    for pattern in (
        r"#\s",
        r"^ERROR: expected value$",
        r"\w+\(\)",
        r"^(?:ERROR|WARN): .+$",
        r"(?:TODO|FIXME)\s*:",
    ):
        assert not bare_token_expressions_in_regex(pattern)
