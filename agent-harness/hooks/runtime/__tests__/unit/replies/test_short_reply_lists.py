import pytest

from human_facing_reply_test_support import (
    labeled_reply_of,
    reply_with_label_word_counts,
    template_violations_in_reply,
)
from end_of_turn_format_guard_test_support import (
    invoke_guard,
    stop_payload,
    write_transcript_with_final_assistant_reply,
)


def list_with_word_counts(word_counts, marker="-"):
    return "\n".join(
        marker + " " + " ".join(["evidence"] * (word_count - 1))
        for word_count in word_counts
    )


@pytest.mark.parametrize("marker", ["-", "*", "+", "1.", "1)"])
@pytest.mark.parametrize("word_count", [20, 25])
def test_three_short_items_are_exempt_from_the_body_budget(marker, word_count):
    short_list = list_with_word_counts([word_count] * 3, marker)
    reply = short_list + "\n\n" + labeled_reply_of(80)

    assert template_violations_in_reply(reply) == []


def test_three_short_items_are_exempt_from_the_confirmation_budget():
    reply = " ".join(["context"] * 100) + "\n\n" + list_with_word_counts([25] * 3)

    assert template_violations_in_reply(reply) == []


def test_three_short_items_are_exempt_from_the_label_budgets():
    reply = reply_with_label_word_counts(session=20, done=20, next_block=10)
    reply += "\n\n" + list_with_word_counts([25] * 3)

    assert template_violations_in_reply(reply) == []


def test_four_items_still_count_toward_the_prose_budget():
    reply = list_with_word_counts([20] * 4) + "\n\n" + labeled_reply_of(80)

    violations = template_violations_in_reply(reply)

    assert any("spends 160 prose words" in violation for violation in violations)


def test_an_oversized_item_keeps_the_whole_list_in_the_prose_budget():
    reply = list_with_word_counts([20, 20, 26]) + "\n\n" + labeled_reply_of(80)

    violations = template_violations_in_reply(reply)

    assert any("spends 146 prose words" in violation for violation in violations)
    assert any("26-word list item" in violation for violation in violations)


def test_list_item_grace_applies_to_lists_that_are_not_exempt():
    reply = list_with_word_counts([25] * 4)

    assert template_violations_in_reply(reply) == []


def test_exempt_lists_still_follow_style_rules():
    reply = "- The result — verified twice."

    assert template_violations_in_reply(reply) == [
        "contains an em dash outside a quotation"
    ]


@pytest.mark.parametrize("label", ["session", "done", "next_block"])
def test_each_label_accepts_exactly_five_words_of_grace(label):
    word_counts = {"session": 10, "done": 5, "next_block": 5}
    word_counts[label] = 30 if label == "session" else 25

    assert (
        template_violations_in_reply(reply_with_label_word_counts(**word_counts)) == []
    )

    word_counts[label] += 1
    violations = template_violations_in_reply(
        reply_with_label_word_counts(**word_counts)
    )

    assert len(violations) == 1
    assert "5-word grace" in violations[0]


def test_stop_guard_accepts_three_short_items_without_a_repair(tmp_path):
    reply = list_with_word_counts([25] * 3) + "\n\n" + labeled_reply_of(80)
    transcript = write_transcript_with_final_assistant_reply(tmp_path, reply)

    result = invoke_guard(stop_payload(transcript))

    assert result.returncode == 0
    assert result.stdout.strip() == ""
