from interactive_humanize_surface_support import (
    HUMANIZE_SKILL_PATH,
    INTERACTIVE_POLICY_PATH,
    interactive_policy_section,
)


def skill_policy():
    return " ".join(HUMANIZE_SKILL_PATH.read_text().split())


def test_reader_recovery_owns_context_without_requiring_a_session_retelling():
    policy = skill_policy()
    assert "full session" in policy
    assert "only the earlier facts needed" in policy
    assert "assume progress updates were unread" in policy
    assert "stop when the request is answered" in policy
    assert "### Interactive session" not in INTERACTIVE_POLICY_PATH.read_text()


def test_work_in_progress_updates_preserve_consumer_authority_only():
    updates = interactive_policy_section("work_in_progress_updates").lower()
    assert "core [evidence]" in updates
    assert "[autonomy]" in updates and "[completion]" in updates
    assert "do not create a second decision or stopping threshold" in updates
    assert "assume progress updates were unread" not in updates


def test_interactive_policy_routes_general_judgment_and_completion_to_core():
    peer = interactive_policy_section("peer_communication").lower()
    completion = interactive_policy_section("exhaust_before_returning").lower()
    assert "core [evidence]" in peer
    assert "core [autonomy]" in completion and "core [completion]" in completion


def test_artifact_links_preserve_the_dotfiles_publication_policy():
    artifacts = interactive_policy_section("artifact_links")
    for required in (
        "Publish local artifacts",
        "full direct URL",
        "CI run",
        "Done line",
    ):
        assert required in artifacts


def test_the_generated_contract_keeps_one_owner_outside_markdown():
    handoff = interactive_policy_section("response_shape")
    for required in (
        "**What is this session about?:**",
        "the whole session's subject and goal",
        "**Done:**",
        "what this round established or changed",
        "**Next:**",
        "required remaining work on this same task",
    ):
        assert required in handoff
    raw_reference = INTERACTIVE_POLICY_PATH.read_text()
    assert "{{reply_format}}" in raw_reference
    for enforced in ("100 prose words", "grace", "data rows", "index column"):
        assert enforced not in raw_reference


def test_requested_form_and_meaning_remain_semantic_obligations():
    policy = skill_policy()
    for required in (
        "Honor requested brevity or form",
        "literal-only output",
        "denominators, bounds, conditions",
        "without changing meaning",
        "Do not disguise ordinary replies as JSON",
    ):
        assert required in policy
    assert "### Concise request" not in INTERACTIVE_POLICY_PATH.read_text()
