from human_facing_reply_test_support import (
    INTERACTIVE_COMMUNICATION_PATH,
    LABELED_REPLY,
    bounce_guidance,
    template_violations_in_reply,
)


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


def test_an_em_dash_in_prose_is_blocked():
    reply = (
        "**what is this session about?:** the gate.\n\n"
        "**done:** the host was removed — the migration is safe.\n\n"
        "**next:** push."
    )

    violations = template_violations_in_reply(reply, "review the migration")

    assert violations == ["contains an em dash outside a quotation"]


def test_an_em_dash_inside_a_quotation_is_preserved():
    reply = (
        "**what is this session about?:** the release note.\n\n"
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
    reply = " ".join(["evidence"] * 81)

    for request in ("explain the architecture", "quick question", "write a full audit"):
        assert template_violations_in_reply(reply, request) == [
            "runs 81 prose words, past the 80-word confirmation, but omits the "
            "What is this session about?:/done:/next: label"
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
