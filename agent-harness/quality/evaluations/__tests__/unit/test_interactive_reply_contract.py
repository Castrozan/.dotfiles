from interactive_humanize_surface_support import (
    interactive_policy_section,
)


def test_interactive_contract_reconstructs_the_whole_session():
    interactive_session = interactive_policy_section("interactive_session")

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
    interactive_session = interactive_policy_section("interactive_session")

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
        "class the reader-recovery evidence recorded; the bounded three-label format "
        "in response-shape carries that recovery instead"
    )


def test_work_in_progress_updates_do_not_require_user_attention():
    work_in_progress_updates = interactive_policy_section("work_in_progress_updates")
    normalized_updates = work_in_progress_updates.lower()

    for required_behavior in (
        "Do not rely on the user reading work-in-progress updates",
        "Assume the user reads only the final reply",
        "core `<evidence>`, `<autonomy>`, and `<completion>`",
        "do not create a second decision or stopping threshold",
        "final reply",
    ):
        assert required_behavior.lower() in normalized_updates

    assert "report new evidence" not in work_in_progress_updates


def test_interactive_policy_routes_general_judgment_and_completion_to_core():
    peer_communication = interactive_policy_section("peer_communication")
    exhaust_before_returning = interactive_policy_section("exhaust_before_returning")

    assert "core `<evidence>`" in peer_communication.lower()
    for authority in ("core `<autonomy>`", "core `<completion>`"):
        assert authority in exhaust_before_returning.lower()

    assert "before defending or retracting" not in peer_communication
    assert "Return only when the task is done" not in exhaust_before_returning


def test_artifact_links_are_remote_and_complete():
    artifact_links = interactive_policy_section("artifact_links")

    for required_behavior in (
        "browser link",
        "merge request",
        "pull request",
        "CI run",
        "report",
        "artifact",
        "Publish local artifacts",
        "full direct URL",
        "local path",
        "commit SHA",
        "ticket key",
        "shorthand reference",
    ):
        assert required_behavior in artifact_links

    assert "needs only the SHA" not in artifact_links


def test_every_substantive_reply_carries_the_three_labels():
    response_shape = interactive_policy_section("response_shape")

    for required_label in (
        "**What is this session about?:**",
        "**Done:**",
        "**Next:**",
    ):
        assert required_label in response_shape

    assert "Bold each label and leave a blank line between the three blocks" in (
        response_shape
    )

    for required_behavior in (
        "40 prose words or fewer is a confirmation",
        "the whole session's subject and goal",
        "never the current step alone",
        "someone who never saw this session can start working",
        "No progress report",
        "required remaining work on this same task",
        "unrelated work",
    ):
        assert required_behavior in response_shape


def test_the_reply_budgets_exempt_visuals_and_never_drop_a_fact():
    response_shape = interactive_policy_section("response_shape")

    for required_budget in (
        "under 100 words",
        "under 120 prose words",
        "within 5 lines and 20 words per line",
        "Visual lines never count",
    ):
        assert required_budget in response_shape

    concise_request = interactive_policy_section("concise_request")
    assert "No budget justifies deleting a fact" in concise_request


def test_concise_request_is_semantic_instead_of_a_global_shape_limit():
    concise_request = interactive_policy_section("concise_request")

    assert "binding" in concise_request
    assert "tldr" in concise_request
    for required_behavior in (
        "stop when the requested outcome is clear",
        "offer to cover material the reader deferred",
    ):
        assert required_behavior in concise_request
    assert "hard ceiling" not in concise_request
    assert "1500" not in concise_request
