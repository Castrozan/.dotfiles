from human_facing_reply_test_support import (
    LABELED_REPLY,
    labeled_reply_of,
    template_violations_in_reply,
)


def test_a_short_confirmation_needs_no_labels():
    reply = "The rebuild is green and the change is live on chise."

    assert template_violations_in_reply(reply, "did it deploy?") == []


def test_a_reply_past_the_confirmation_names_the_labels_it_omits():
    violations = template_violations_in_reply(
        " ".join(["evidence"] * 60), "explain the architecture"
    )

    assert violations == [
        "runs 60 prose words, past the 40-word confirmation, but omits the "
        "brief:/done:/next: label"
    ]


def test_a_partially_labeled_reply_names_only_the_missing_label():
    reply = f"**brief:** the release gate.\n\n**done:** {' '.join(['evidence'] * 50)}"

    violations = template_violations_in_reply(reply, "where does it stand?")

    assert violations == [
        "runs 55 prose words, past the 40-word confirmation, but omits the next: label"
    ]


def test_a_labeled_reply_within_both_budgets_passes():
    assert template_violations_in_reply(labeled_reply_of(40), "status?") == []


def test_prose_past_the_word_ceiling_is_blocked():
    violations = template_violations_in_reply(labeled_reply_of(130), "status?")

    assert any("past the 120-word ceiling" in violation for violation in violations)


def test_labeled_sections_past_their_budget_are_blocked():
    violations = template_violations_in_reply(labeled_reply_of(105), "status?")

    assert any("100-word budget" in violation for violation in violations)


def test_a_table_is_exempt_from_the_word_count():
    table_rows = "\n".join(["| " + " | ".join(["measured"] * 8) + " |"] * 40)
    reply = f"{LABELED_REPLY}\n\n{table_rows}"

    assert template_violations_in_reply(reply, "compare the arms") == []


def test_a_tree_or_diagram_is_exempt_from_the_word_count():
    tree_lines = "\n".join(["├── one module owning one measured responsibility"] * 40)
    reply = f"{LABELED_REPLY}\n\n{tree_lines}"

    assert template_violations_in_reply(reply, "who owns what?") == []


def test_a_list_past_five_lines_is_blocked():
    reply = f"{LABELED_REPLY}\n\n" + "\n".join(["- one finding"] * 6)

    violations = template_violations_in_reply(reply, "what did you find?")

    assert violations == ["stacks 6 list lines, past the 5-line ceiling for one list"]


def test_a_list_line_past_twenty_words_is_blocked():
    long_line = "- " + " ".join(["evidence"] * 21)
    reply = f"{LABELED_REPLY}\n\n{long_line}"

    violations = template_violations_in_reply(reply, "what did you find?")

    assert violations == [
        "runs a 22-word list line, past the 20-word ceiling for one line"
    ]


def test_five_short_list_lines_pass():
    reply = f"{LABELED_REPLY}\n\n" + "\n".join(["- one finding"] * 5)

    assert template_violations_in_reply(reply, "what did you find?") == []


def test_a_label_without_bold_emphasis_is_blocked():
    reply = (
        "brief: the release gate that decides whether the candidate policy ships.\n\n"
        "done: measured the candidate against the control across three epochs and "
        "recorded the paired interval.\n\n"
        "next: commit the refreshed baseline, then let the steward reconcile the "
        "diverged branch on its own loop."
    )

    assert template_violations_in_reply(reply, "status?") == [
        "writes the brief: label without bold emphasis"
    ]


def test_labels_crammed_into_one_block_are_blocked():
    reply = (
        "**brief:** the release gate that decides whether the candidate policy ships.\n"
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
