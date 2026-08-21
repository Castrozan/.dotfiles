from interactive_humanize_surface_support import (
    interactive_policy_section,
)


def test_interactive_contract_reconstructs_the_whole_session():
    interactive_session = interactive_policy_section("interactive-session")

    for required_context in (
        "multitasks",
        "may forget what the session is about",
        "whole session",
        "work-in-progress updates",
        "previous interaction",
        "earlier conversation",
    ):
        assert required_context in interactive_session

    for unrelated_session_type in (
        "background agents",
        "clawde",
        "headless runs",
        "subagents",
    ):
        assert unrelated_session_type not in interactive_session


def test_standalone_recovery_does_not_license_restating_the_session():
    interactive_session = interactive_policy_section("interactive-session")

    for required_behavior in (
        "not that it retells the whole session",
        "at the length that answer needs",
    ):
        assert required_behavior in interactive_session

    assert "state the overall task, the result or current state" not in (
        interactive_session
    ), (
        "an unbounded task, state, evidence, and remaining-work recital turns standalone "
        "recovery into a per-turn session retelling, which is the pure-verbosity failure "
        "class the reader-recovery evidence recorded; the bounded brief/done/next format "
        "in response-shape carries that recovery instead"
    )


def test_work_in_progress_updates_do_not_require_user_attention():
    work_in_progress_updates = interactive_policy_section("work-in-progress-updates")

    for required_behavior in (
        "Do not rely on the user reading work-in-progress updates",
        "best-supported decision",
        "within the task's scope",
        "require new authority",
        "final reply",
    ):
        assert required_behavior in work_in_progress_updates

    assert "report new evidence" not in work_in_progress_updates


def test_artifact_links_are_remote_and_complete():
    artifact_links = interactive_policy_section("artifact-links")

    for required_behavior in (
        "only through remote links",
        "Push every artifact",
        "full direct URL",
        "local path",
        "commit SHA",
        "ticket key",
        "shorthand reference",
    ):
        assert required_behavior in artifact_links

    assert "needs only the SHA" not in artifact_links


def test_every_substantive_reply_carries_the_three_labels():
    response_shape = interactive_policy_section("response-shape")

    for required_label in ("**Brief:**", "**Done:**", "**Next:**"):
        assert required_label in response_shape

    assert "Bold each label and leave a blank line between the three blocks" in (
        response_shape
    )

    for required_behavior in (
        "40 prose words or fewer is a confirmation",
        "stay true next week",
        "No recency bias",
        "required remaining work on this same task",
        "unrelated work",
    ):
        assert required_behavior in response_shape


def test_the_reply_budgets_exempt_visuals_and_never_drop_a_fact():
    response_shape = interactive_policy_section("response-shape")

    for required_budget in (
        "under 100 words",
        "under 120 prose words",
        "within 5 lines and 20 words per line",
        "Visual lines never count",
    ):
        assert required_budget in response_shape

    concise_request = interactive_policy_section("concise-request")
    assert "No budget justifies deleting a fact" in concise_request


def test_concise_request_is_semantic_instead_of_a_global_shape_limit():
    concise_request = interactive_policy_section("concise-request")

    assert "binding" in concise_request
    assert "tldr" in concise_request
    for required_behavior in (
        "stop when the requested outcome is clear",
        "offer to cover material the reader deferred",
    ):
        assert required_behavior in concise_request
    assert "hard ceiling" not in concise_request
    assert "1500" not in concise_request
