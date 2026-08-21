import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = HOOKS_ROOT.parents[2]
REPLY_RULE_MODULE_DIRECTORY = next(HOOKS_ROOT.rglob("reply_rule_catalog.py")).parent
if str(REPLY_RULE_MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(REPLY_RULE_MODULE_DIRECTORY))

from reply_rule_catalog import template_violations_in_reply  # noqa: E402
from reply_rule_feedback import bounce_guidance  # noqa: E402

INTERACTIVE_COMMUNICATION_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "humanize"
    / "interactive-communication.md"
)

LABELED_REPLY = (
    "**brief:** the release gate.\n\n"
    "**done:** measured the candidate.\n\n"
    "**next:** push."
)


def labeled_reply_of(prose_words: int) -> str:
    body = " ".join(["evidence"] * prose_words)
    return f"**brief:** the release gate.\n\n**done:** {body}\n\n**next:** push."


def test_named_merge_request_without_a_direct_link_is_blocked():
    violations = template_violations_in_reply(
        "MR !41 is ready for review.", "is the change ready?"
    )

    assert violations == ["names an MR or PR but gives no link to validate it"]


def test_named_pull_request_with_a_direct_link_passes():
    reply = "PR #17 is ready: https://github.com/example/project/pull/17"

    assert template_violations_in_reply(reply, "is the change ready?") == []


def test_generic_merge_and_pull_request_terms_do_not_claim_an_artifact():
    reply = (
        "Pull request paths now trigger CI. The guide also explains how to open a "
        "merge request."
    )

    assert template_violations_in_reply(reply, "what changed in CI?") == []


def test_a_quoted_unlinked_artifact_inside_a_fence_does_not_block():
    reply = "The source says:\n```\nMR !41 is pending\n```\nNo artifact is named in my prose."

    assert template_violations_in_reply(reply, "quote the source") == []


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


def test_an_em_dash_in_prose_is_blocked():
    reply = (
        "**brief:** the gate.\n\n"
        "**done:** the host was removed — the migration is safe.\n\n"
        "**next:** push."
    )

    violations = template_violations_in_reply(reply, "review the migration")

    assert violations == ["contains an em dash outside a quotation"]


def test_an_em_dash_inside_a_quotation_is_preserved():
    reply = (
        "**brief:** the release note.\n\n"
        '**done:** quoted exactly, "Retries are bounded — the worker stops after '
        'attempt three."\n\n'
        "**next:** publish it."
    )

    assert template_violations_in_reply(reply, "quote the note") == []


def test_reaction_and_narration_openers_are_blocked():
    assert template_violations_in_reply("Sure, the host is gone.", "is it gone?") == [
        "opens with a reaction or sycophancy phrase"
    ]
    assert template_violations_in_reply("Let me check the host.", "is it gone?") == [
        "opens by narrating what you are about to do"
    ]


def test_section_headers_remain_available():
    reply = f"## Decision\n\n{LABELED_REPLY}"

    assert template_violations_in_reply(reply, "review the migration") == []


def test_the_request_text_no_longer_gates_any_rule():
    reply = " ".join(["evidence"] * 60)

    for request in ("explain the architecture", "quick question", "write a full audit"):
        assert template_violations_in_reply(reply, request) == [
            "runs 60 prose words, past the 40-word confirmation, but omits the "
            "brief:/done:/next: label"
        ]


def test_bounce_guidance_names_the_violation_and_routes_to_humanize():
    guidance = bounce_guidance(["names an MR or PR but gives no link to validate it"])

    assert "names an MR or PR" in guidance
    assert "load the humanize skill" in guidance.lower()
    assert "interactive communication instructions" in guidance


def test_interactive_instructions_route_substantive_output_to_humanize():
    policy = INTERACTIVE_COMMUNICATION_PATH.read_text(encoding="utf-8").lower()

    assert "load the humanize skill" in policy
    for reader_task in (
        "explanation",
        "diagnosis",
        "decision",
        "warning",
        "report",
        "summary",
    ):
        assert reader_task in policy


def test_interactive_contract_treats_explicit_short_requests_as_binding():
    policy = INTERACTIVE_COMMUNICATION_PATH.read_text(encoding="utf-8").lower()

    assert "tldr" in policy
    assert "binding" in policy


def test_a_label_without_bold_emphasis_is_blocked():
    reply = "brief: the gate.\n\ndone: measured the candidate.\n\nnext: push."

    assert template_violations_in_reply(reply, "status?") == [
        "writes the brief: label without bold emphasis"
    ]


def test_labels_crammed_into_one_block_are_blocked():
    reply = "**brief:** the gate.\n**done:** measured it.\n**next:** push."

    assert template_violations_in_reply(reply, "status?") == [
        "runs the done: label into the line above it instead of starting its own block"
    ]


def test_a_label_word_inside_a_fence_is_not_a_reply_label():
    reply = (
        "The log line reads:\n```\nnext: retry scheduled\n```\nNothing else changed."
    )

    assert template_violations_in_reply(reply, "what did the log say?") == []
