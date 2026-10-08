import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/speech_text.py"
SPECIFICATION = importlib.util.spec_from_file_location("speech_text", SCRIPT)
speech_text = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(speech_text)


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        (
            "**Nightly_failed**: `no_comments_in_code` 34/35",
            "Nightly failed : no comments in code 34 out of 35",
        ),
        (
            "## Critical\n- Disk_usage is 95% & rising",
            "Critical Disk usage is 95 percent and rising",
        ),
        ("```python\nno_comments_in_code 42\n```", "no comments in code 42"),
        (
            "[Issue 42](https://example.test/42) needs_attention",
            "Issue 42 needs attention",
        ),
        (
            "<b>Ação necessária</b> — serviço_indisponível",
            "Ação necessária serviço indisponível",
        ),
        (
            "Latency <500 ms, version 3.12, tests 1-3",
            "Latency less than 500 ms, version 3.12, tests 1 to 3",
        ),
        (
            "Temperature -5.2, load &gt;= 90%",
            "Temperature minus 5.2, load greater than or equal to 90 percent",
        ),
        ("src/module_name.py failed", "src module name py failed"),
    ],
)
def test_sanitizes_plain_speech_preserving_words_and_numbers(message, expected):
    assert speech_text.sanitize_speech(message) == expected


@pytest.mark.parametrize(
    "message",
    [
        "API_KEY=synthetic-test-value",
        "password: synthetic-test-value",
        "Bearer synthetic-test-value",
        "access_token=synthetic-test-value",
        "-----BEGIN PRIVATE KEY-----",
        "sk-syntheticTestValue",
        "ghp_syntheticTestValue",
        "eyJsynthetic.header.signature",
        "sensitivevalue012345678901234567890123456789",
        "&lt;secret&gt;synthetic-test-value&lt;/secret&gt;",
        "ＡＰＩ＿ＫＥＹ synthetic-test-value",
        "___ ** ```",
        "",
    ],
)
def test_sensitive_or_empty_payloads_cannot_be_spoken(message):
    assert speech_text.sanitize_speech(message) is None
