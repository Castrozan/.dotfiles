from interactive_surface_support import interactive_policy_section


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
