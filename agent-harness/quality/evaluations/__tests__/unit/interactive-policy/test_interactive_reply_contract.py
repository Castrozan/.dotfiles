from interactive_surface_support import interactive_policy_section


def test_artifact_links_preserve_the_dotfiles_publication_policy():
    artifacts = interactive_policy_section("artifact_links")
    for required in (
        "Publish local artifacts",
        "full direct URL",
        "CI run",
        "Done line",
    ):
        assert required in artifacts
