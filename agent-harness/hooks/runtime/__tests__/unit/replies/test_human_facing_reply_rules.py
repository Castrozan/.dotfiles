from human_facing_reply_test_support import (
    LABELED_REPLY,
    labeled_reply_of,
    reply_with_label_word_counts,
    template_violations_in_reply,
)


def test_a_hundred_word_confirmation_needs_no_labels():
    reply = " ".join(["evidence"] * 100)

    assert template_violations_in_reply(reply) == []


def test_a_reply_past_the_confirmation_and_its_grace_names_the_labels_it_omits():
    violations = template_violations_in_reply(" ".join(["evidence"] * 111))

    assert violations == [
        "runs 111 prose words, past the 100-word confirmation, but omits the "
        "What is this session about?:/done:/next: label",
        "spends 111 prose words above the labels, past their own 80-word budget and "
        "its 10-word grace; move suitable detail into a short list, table, tree or "
        "diagram, which is not counted",
    ]


def test_a_reply_inside_the_confirmation_grace_still_needs_no_labels():
    assert template_violations_in_reply(" ".join(["evidence"] * 110)) == []


def test_a_partially_labeled_reply_names_only_the_missing_label():
    body = " ".join(["evidence"] * 80)
    session = " ".join(["evidence"] * 15)
    done = " ".join(["evidence"] * 14)
    reply = f"{body}\n\n**what is this session about?:** {session}\n\n**done:** {done}"

    violations = template_violations_in_reply(reply)

    assert violations == [
        "runs 115 prose words, past the 100-word confirmation, but omits the next: label"
    ]


def test_a_labeled_reply_within_both_budgets_passes():
    assert template_violations_in_reply(labeled_reply_of(40)) == []


def test_prose_above_the_labels_past_its_budget_and_grace_is_blocked():
    violations = template_violations_in_reply(labeled_reply_of(100))

    assert any("past their own 80-word budget" in violation for violation in violations)


def test_prose_above_the_labels_inside_the_grace_passes():
    violations = template_violations_in_reply(labeled_reply_of(90))

    assert not any(
        "past their own 80-word budget" in violation for violation in violations
    )


def test_labeled_sections_past_their_shared_budget_and_grace_are_blocked():
    reply = reply_with_label_word_counts(session=25, done=20, next_block=20)

    violations = template_violations_in_reply(reply)

    assert any("50-word budget" in violation for violation in violations)


def test_labeled_sections_inside_the_shared_grace_pass():
    reply = reply_with_label_word_counts(session=20, done=20, next_block=20)

    violations = template_violations_in_reply(reply)

    assert not any("50-word budget" in violation for violation in violations)


def test_one_label_past_its_own_budget_and_grace_is_blocked():
    reply = reply_with_label_word_counts(session=10, done=26, next_block=5)

    assert template_violations_in_reply(reply) == [
        "spends 26 words on the done: block, past its 20-word budget and its "
        "5-word grace"
    ]


def test_one_label_inside_its_own_grace_passes():
    reply = reply_with_label_word_counts(session=10, done=25, next_block=5)

    assert template_violations_in_reply(reply) == []


def test_a_table_is_exempt_from_the_word_count():
    table_rows = "\n".join(["| " + " | ".join(["measured"] * 8) + " |"] * 40)
    reply = f"{LABELED_REPLY}\n\n{table_rows}"

    assert template_violations_in_reply(reply) == []


def test_a_tree_or_diagram_is_exempt_from_the_word_count():
    tree_lines = "\n".join(["├── one module owning one measured responsibility"] * 40)
    reply = f"{LABELED_REPLY}\n\n{tree_lines}"

    assert template_violations_in_reply(reply) == []


def test_a_list_past_five_lines_is_blocked():
    reply = "\n".join(["- one finding"] * 6) + f"\n\n{LABELED_REPLY}"

    violations = template_violations_in_reply(reply)

    assert violations == ["stacks 6 list lines, past the 5-line ceiling for one list"]


def test_a_list_line_past_twenty_words_and_its_grace_is_blocked():
    long_line = "- " + " ".join(["evidence"] * 25)
    reply = f"{long_line}\n\n{LABELED_REPLY}"

    violations = template_violations_in_reply(reply)

    assert violations == [
        "runs a 26-word list line, past the 20-word ceiling and its 5-word grace "
        "for one line"
    ]


def test_five_short_list_lines_pass():
    reply = "\n".join(["- one finding"] * 5) + f"\n\n{LABELED_REPLY}"

    assert template_violations_in_reply(reply) == []


def test_a_label_without_bold_emphasis_is_blocked():
    context = " ".join(["evidence"] * 65)
    reply = (
        f"{context}\n\n"
        "what is this session about?: the release gate that decides whether the "
        "candidate policy ships.\n\n"
        "done: measured the candidate against the control across three epochs and "
        "recorded the paired interval.\n\n"
        "next: commit the refreshed baseline, then let the steward reconcile the "
        "diverged branch on its own loop."
    )

    assert template_violations_in_reply(reply) == [
        "writes the What is this session about?: label without bold emphasis"
    ]


def test_labels_crammed_into_one_block_are_blocked():
    context = " ".join(["evidence"] * 65)
    reply = (
        f"{context}\n\n"
        "**what is this session about?:** the release gate that decides whether the "
        "candidate policy ships.\n"
        "**done:** measured the candidate against the control across three epochs and "
        "recorded the paired interval.\n"
        "**next:** commit the refreshed baseline, then let the steward reconcile the "
        "diverged branch on its own loop."
    )

    assert template_violations_in_reply(reply) == [
        "runs the done: label into the line above it instead of starting its own block"
    ]


def test_a_label_word_inside_a_fence_is_not_a_reply_label():
    reply = (
        "The log line reads:\n```\nnext: retry scheduled\n```\nNothing else changed."
    )

    assert template_violations_in_reply(reply) == []
