from human_facing_reply_test_support import (
    LABELED_REPLY,
    labeled_reply_of,
    reply_with_label_word_counts,
    template_violations_in_reply,
)


def test_a_hundred_word_confirmation_needs_no_labels():
    reply = " ".join(["evidence"] * 100)

    assert template_violations_in_reply(reply, "did it deploy?") == []


def test_a_reply_past_the_confirmation_names_the_labels_it_omits():
    violations = template_violations_in_reply(
        " ".join(["evidence"] * 101), "explain the architecture"
    )

    assert violations == [
        "runs 101 prose words, past the 100-word confirmation, but omits the "
        "What is this session about?:/done:/next: label",
        "spends 101 prose words above the labels, past their own 80-word budget; "
        "move the detail into a table, tree or diagram, which is not counted",
    ]


def test_a_partially_labeled_reply_names_only_the_missing_label():
    body = " ".join(["evidence"] * 80)
    session = " ".join(["evidence"] * 15)
    done = " ".join(["evidence"] * 14)
    reply = f"{body}\n\n**what is this session about?:** {session}\n\n**done:** {done}"

    violations = template_violations_in_reply(reply, "where does it stand?")

    assert violations == [
        "runs 115 prose words, past the 100-word confirmation, but omits the next: label"
    ]


def test_a_labeled_reply_within_both_budgets_passes():
    assert template_violations_in_reply(labeled_reply_of(40), "status?") == []


def test_prose_above_the_labels_past_its_own_budget_is_blocked():
    violations = template_violations_in_reply(labeled_reply_of(90), "status?")

    assert any("past their own 80-word budget" in violation for violation in violations)


def test_labeled_sections_past_their_shared_budget_are_blocked():
    reply = reply_with_label_word_counts(session=25, done=15, next_block=15)

    violations = template_violations_in_reply(reply, "status?")

    assert any("50-word budget" in violation for violation in violations)


def test_one_label_past_its_own_budget_is_blocked():
    reply = reply_with_label_word_counts(session=10, done=21, next_block=5)

    assert template_violations_in_reply(reply, "status?") == [
        "spends 21 words on the done: block, past its 20-word budget"
    ]


def test_a_table_is_exempt_from_the_word_count():
    table_rows = "\n".join(["| " + " | ".join(["measured"] * 8) + " |"] * 40)
    reply = f"{LABELED_REPLY}\n\n{table_rows}"

    assert template_violations_in_reply(reply, "compare the arms") == []


def test_a_tree_or_diagram_is_exempt_from_the_word_count():
    tree_lines = "\n".join(["├── one module owning one measured responsibility"] * 40)
    reply = f"{LABELED_REPLY}\n\n{tree_lines}"

    assert template_violations_in_reply(reply, "who owns what?") == []


def test_a_list_past_five_lines_is_blocked():
    reply = "\n".join(["- one finding"] * 6) + f"\n\n{LABELED_REPLY}"

    violations = template_violations_in_reply(reply, "what did you find?")

    assert violations == ["stacks 6 list lines, past the 5-line ceiling for one list"]


def test_a_list_line_past_twenty_words_is_blocked():
    long_line = "- " + " ".join(["evidence"] * 21)
    reply = f"{long_line}\n\n{LABELED_REPLY}"

    violations = template_violations_in_reply(reply, "what did you find?")

    assert violations == [
        "runs a 22-word list line, past the 20-word ceiling for one line"
    ]


def test_five_short_list_lines_pass():
    reply = "\n".join(["- one finding"] * 5) + f"\n\n{LABELED_REPLY}"

    assert template_violations_in_reply(reply, "what did you find?") == []


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

    assert template_violations_in_reply(reply, "status?") == [
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

    assert template_violations_in_reply(reply, "status?") == [
        "runs the done: label into the line above it instead of starting its own block"
    ]


def test_a_label_word_inside_a_fence_is_not_a_reply_label():
    reply = (
        "The log line reads:\n```\nnext: retry scheduled\n```\nNothing else changed."
    )

    assert template_violations_in_reply(reply, "what did the log say?") == []
