from human_facing_reply_test_support import template_violations_in_reply
from reply_mechanical_repairs import repaired_reply_text


def test_an_em_dash_between_clauses_becomes_a_comma():
    reply = (
        "**what is this session about?:** the gate.\n\n"
        "**done:** the host was removed — the migration is safe.\n\n"
        "**next:** push."
    )

    repaired = repaired_reply_text(reply)

    assert "the host was removed, the migration is safe." in repaired
    assert template_violations_in_reply(repaired, "review the migration") == []


def test_an_en_dash_between_numbers_becomes_a_hyphen():
    assert repaired_reply_text("retries 3–5 stay bounded.") == (
        "retries 3-5 stay bounded."
    )


def test_a_dash_inside_a_quotation_or_code_span_is_preserved():
    reply = 'the note says "bounded — capped" and `a — b` stays.'

    assert repaired_reply_text(reply) == reply


def test_a_dash_inside_a_fenced_block_is_preserved():
    reply = "prose stays clean.\n```\nvalue — other\n```\n"

    assert repaired_reply_text(reply) == reply


def test_an_unemphasized_label_gains_bold_emphasis():
    reply = (
        "**what is this session about?:** the gate.\n\n"
        "done: measured the candidate.\n\n"
        "**next:** push."
    )

    repaired = repaired_reply_text(reply)

    assert "**done:** measured the candidate." in repaired
    assert template_violations_in_reply(repaired, "measure it") == []


def test_a_label_running_into_the_line_above_gains_its_own_block():
    reply = (
        "**what is this session about?:** the gate.\n"
        "**done:** measured the candidate.\n"
        "**next:** push."
    )

    repaired = repaired_reply_text(reply)

    assert template_violations_in_reply(repaired, "measure it") == []
    assert repaired.count("\n\n") == 2


def test_a_compliant_reply_is_left_untouched():
    reply = (
        "**what is this session about?:** the gate.\n\n"
        "**done:** measured the candidate.\n\n"
        "**next:** push."
    )

    assert repaired_reply_text(reply) == reply


def test_a_dash_free_overlong_reply_is_not_repairable():
    reply = "word " * 400

    assert repaired_reply_text(reply) == reply


def test_a_leading_dash_does_not_leave_a_comma_opening_the_line():
    assert repaired_reply_text("- — the gate holds") == "- the gate holds"


def test_a_trailing_dash_does_not_leave_a_comma_ending_the_line():
    assert repaired_reply_text("the gate holds —") == "the gate holds"
