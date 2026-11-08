from instructions.instruction_surface_scanner import REPO_ROOT, frontmatter_key_values


CORE_COMMUNICATION_DIRECTORY = (
    REPO_ROOT / "agent-harness" / "agent-instructions" / "core-rules" / "communication"
)
HUMANIZE_DIRECTORY = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "writing"
    / "humanize"
)
HUMANIZE_SKILL_PATH = HUMANIZE_DIRECTORY / "SKILL.md"
HUMANIZE_CASE_EXAMPLES = (
    "readme.md",
    "pull-request.md",
    "handoff.md",
    "chat-message.md",
    "email.md",
    "long-lived-docs.md",
    "bug-report.md",
    "status-update.md",
    "release-notes.md",
)
MAXIMUM_HUMANIZE_SKILL_BYTES = 6000

REMOVED_GENERATED_SURFACES = (
    CORE_COMMUNICATION_DIRECTORY / "interactive-human-communication.md",
    CORE_COMMUNICATION_DIRECTORY / "interactive-hook-communication.md",
    HUMANIZE_DIRECTORY / "enforced-wording-rules.md",
    CORE_COMMUNICATION_DIRECTORY / "render-human-communication-markdown.py",
)


def test_humanize_owns_documents_read_later_and_defers_live_replies():
    humanize_skill = HUMANIZE_SKILL_PATH.read_text(encoding="utf-8")
    description = (frontmatter_key_values(humanize_skill) or {}).get("description", "")

    assert "outside a live session" in description
    assert "Not for live session replies" in description
    for owner in ("`wellput`", "`coding`"):
        assert owner in humanize_skill
    for retired_section in (
        "### Confusion recovery",
        "### Human register",
        "### Interactive communication",
    ):
        assert retired_section not in humanize_skill
    assert not (
        HUMANIZE_DIRECTORY / "references" / "interactive-communication.md"
    ).exists()

    humanize_skill_bytes = len(humanize_skill.encode("utf-8"))
    assert humanize_skill_bytes <= MAXIMUM_HUMANIZE_SKILL_BYTES, (
        "the on-demand Humanize skill must stay compact; it now costs "
        f"{humanize_skill_bytes} bytes"
    )


def test_humanize_links_a_worked_example_for_every_case():
    humanize_skill = HUMANIZE_SKILL_PATH.read_text(encoding="utf-8")

    for example in HUMANIZE_CASE_EXAMPLES:
        assert f"](examples/{example})" in humanize_skill
        assert (HUMANIZE_DIRECTORY / "examples" / example).is_file()
        assert "\n```" in (HUMANIZE_DIRECTORY / "examples" / example).read_text(
            encoding="utf-8"
        )


def test_no_generated_policy_surface_sits_between_owners_and_consumers():
    assert not [path for path in REMOVED_GENERATED_SURFACES if path.exists()]


def test_superseded_split_interactive_surfaces_are_removed():
    assert not (CORE_COMMUNICATION_DIRECTORY / "interactive-preferences.md").exists()
    assert not (CORE_COMMUNICATION_DIRECTORY / "enforced-reply-rules.md").exists()
