import itertools

import pytest

from human_facing_reply_test_support import (
    labeled_reply_of,
    reply_with_label_word_counts,
    template_violations_in_reply,
)


@pytest.mark.parametrize("prefix,suffix", [("| ", ""), ("", " │")])
def test_visual_characters_do_not_turn_prose_into_a_diagram(prefix, suffix):
    reply = prefix + "evidence " * 300 + suffix

    assert template_violations_in_reply(reply)


@pytest.mark.parametrize(
    "reply",
    [
        "- " + "evidence " * 9 + "\n  " + "evidence " * 90,
        "\n".join("- evidence\n  continuation" for _ in range(6)),
    ],
)
def test_continuations_do_not_split_one_item_or_list_into_short_lists(reply):
    assert any("list" in violation for violation in template_violations_in_reply(reply))


@pytest.mark.parametrize(
    "separator", ["\n\n| Result |\n| --- |\n| passed |\n\n", "\n\n"]
)
def test_separate_markdown_lists_keep_separate_budgets(separator):
    bullets = "\n".join("- " + "evidence " * 19 for _ in range(3))
    numbered = "\n".join("1. " + "evidence " * 19 for _ in range(3))

    assert template_violations_in_reply(bullets + separator + numbered) == []


@pytest.mark.parametrize("order", list(itertools.permutations(range(3))))
def test_long_reply_requires_the_configured_label_order(order):
    blocks = reply_with_label_word_counts(20, 20, 10).split("\n\n")
    reply = "evidence " * 80 + "\n\n" + "\n\n".join(blocks[index] for index in order)

    violations = template_violations_in_reply(reply)

    assert bool(violations) == (order != (0, 1, 2))


def test_long_reply_rejects_duplicate_labels_within_the_word_budgets():
    reply = "evidence " * 80 + "\n\n" + reply_with_label_word_counts(20, 20, 10)

    assert template_violations_in_reply(reply + "\n\n**Done:** extra")


def test_unclosed_bold_markup_does_not_emphasize_a_label():
    reply = "evidence " * 80 + "\n\n" + reply_with_label_word_counts(20, 20, 10)

    violations = template_violations_in_reply(reply.replace(":**", ":"))

    assert any("without bold" in violation for violation in violations)


def test_alternative_commonmark_strong_delimiters_emphasize_labels():
    reply = "evidence " * 80 + "\n\n" + reply_with_label_word_counts(20, 20, 10)

    assert template_violations_in_reply(reply.replace("**", "__")) == []


@pytest.mark.parametrize("fence", ["```", "~~~", "````"])
def test_commonmark_fenced_diffs_are_exempt(fence):
    reply = fence + "diff\n+ " + "evidence " * 300 + "\n" + fence

    assert template_violations_in_reply(reply) == []


def test_gfm_tables_without_outer_pipes_are_exempt():
    reply = "Result | Details\n--- | ---\nPassed | " + "evidence " * 150

    assert template_violations_in_reply(reply) == []


def test_list_exemption_does_not_hide_style_violations():
    assert template_violations_in_reply("- **Sure**, the check passed.")


@pytest.mark.parametrize(
    "opener", ["**Sure**, done.", "**Let me** check.", "I’ll now check."]
)
def test_opener_restrictions_use_rendered_text(opener):
    assert template_violations_in_reply(opener)


@pytest.mark.parametrize("quote", [("'", "'"), ('"', '"'), ("‘", "’"), ("“", "”")])
def test_balanced_quotations_preserve_quoted_dashes(quote):
    reply = "The source says " + quote[0] + "The result — verified." + quote[1]

    assert template_violations_in_reply(reply) == []


def test_apostrophes_do_not_hide_unquoted_dashes():
    assert template_violations_in_reply("The user's result — isn't verified.")


def test_visuals_preserve_the_body_and_label_boundaries():
    reply = labeled_reply_of(90) + "\n\n~~~text\n" + "visual " * 300 + "\n~~~"

    assert template_violations_in_reply(reply) == []


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_source_line_mapping_preserves_commonmark_line_endings(newline):
    reply = labeled_reply_of(90).replace("\n", newline)

    assert template_violations_in_reply(reply) == []


def test_a_quoted_reaction_is_not_the_assistants_opener():
    assert (
        template_violations_in_reply(
            "> Sure, the source says this.\n\nThe result is ready."
        )
        == []
    )
