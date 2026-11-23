import pytest
from instructions.ai_instruction_format import inspect_markdown_instruction


def sentence_of(word_count):
    return " ".join(["Every"] + ["word"] * (word_count - 2) + ["counts."])


def findings(text):
    inspected = inspect_markdown_instruction(text)
    return (
        [(finding.rule, finding.line_number) for finding in inspected.violations],
        [(finding.rule, finding.line_number) for finding in inspected.warnings],
    )


@pytest.mark.parametrize(
    ("word_count", "expected"),
    [
        (25, ([], [])),
        (26, ([], [("instruction_sentence_word_advice", 3)])),
        (40, ([], [("instruction_sentence_word_advice", 3)])),
        (41, ([("instruction_sentence_word_limit", 3)], [])),
    ],
)
def test_warns_past_twenty_five_words_and_rejects_past_forty(word_count, expected):
    assert findings(f"### Evidence\n\n{sentence_of(word_count)}\n") == expected


def test_reports_the_source_line_where_the_long_sentence_starts():
    text = f"### Evidence\n\nRead the source. Then\n{sentence_of(41)}\n"
    assert findings(text) == ([("instruction_sentence_word_limit", 3)], [])
    text = f"### Evidence\n\nRead the source.\n{sentence_of(41)}\n"
    assert findings(text) == ([("instruction_sentence_word_limit", 4)], [])


def test_counts_inline_code_as_one_word():
    code = "`" + " ".join("token" for _ in range(30)) + "`"
    assert findings(f"### Evidence\n\nRun {code} first.\n") == ([], [])


def test_a_sentence_may_start_with_inline_code():
    first = sentence_of(20)
    second = "`tool --flag` " + " ".join(["word"] * 20) + " ends."
    assert findings(f"### Evidence\n\n{first} {second}\n") == ([], [])
