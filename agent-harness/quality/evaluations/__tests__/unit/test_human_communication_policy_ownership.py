from instruction_surface_scanner import REPO_ROOT, frontmatter_key_values


HOOK_DOMAIN_DIRECTORY = (
    REPO_ROOT / "agent-harness" / "hooks" / "runtime" / "common" / "human_facing_reply"
)
CORE_COMMUNICATION_DIRECTORY = (
    REPO_ROOT / "agent-harness" / "agent-instructions" / "core-rules" / "communication"
)
HUMANIZE_DIRECTORY = (
    REPO_ROOT / "agent-harness" / "agent-instructions" / "skills" / "humanize"
)
HUMANIZE_SKILL_PATH = HUMANIZE_DIRECTORY / "SKILL.md"
INTERACTIVE_POLICY_PATH = HUMANIZE_DIRECTORY / "interactive-communication.md"
COMMUNITY_LANGUAGE_PATH = HUMANIZE_DIRECTORY / "community-language.md"
REPLY_RULE_CATALOG_PATH = HOOK_DOMAIN_DIRECTORY / "reply_rule_catalog.py"
REPLY_RULE_FEEDBACK_PATH = HOOK_DOMAIN_DIRECTORY / "reply_rule_feedback.py"
MAXIMUM_COMMUNITY_LANGUAGE_BYTES = 10000

REMOVED_GENERATED_SURFACES = (
    CORE_COMMUNICATION_DIRECTORY / "interactive-human-communication.md",
    CORE_COMMUNICATION_DIRECTORY / "interactive-hook-communication.md",
    HUMANIZE_DIRECTORY / "enforced-wording-rules.md",
    CORE_COMMUNICATION_DIRECTORY / "render-human-communication-markdown.py",
)


def test_humanize_package_owns_interactive_and_output_policies():
    interactive_policy = INTERACTIVE_POLICY_PATH.read_text(encoding="utf-8")
    humanize_skill = HUMANIZE_SKILL_PATH.read_text(encoding="utf-8")
    community_language = COMMUNITY_LANGUAGE_PATH.read_text(encoding="utf-8")

    for tag in (
        "interactive-session",
        "humanize-policy-loading",
        "peer-communication",
        "work-in-progress-updates",
        "artifact-links",
        "exhaust-before-returning",
        "reply_template",
        "request_gated",
    ):
        assert f"<{tag}>" in interactive_policy

    assert "<always_enforced>" not in interactive_policy

    for tag in (
        "human-readable-output",
        "reader-outcome",
        "epistemic-clarity",
        "representation-selection",
        "term-discipline",
        "sentence-construction",
        "meaning-preservation",
        "human-voice",
        "revision-pass",
        "commit_message",
        "pull_or_merge_request",
        "ticket_comment",
        "report_document_or_page",
        "binds_every_human_facing_channel",
    ):
        assert f"<{tag}>" in humanize_skill

    for tag in (
        "community-language-calibration",
        "example-selection",
        "explain-by-contrast",
        "diagnose-from-evidence",
        "decide-by-tradeoff",
        "warn-with-condition",
        "report-measured-change",
        "summarize-for-action",
        "meaning-recovery-check",
        "community-provenance",
    ):
        assert f"<{tag}>" in community_language

    for reader_task in (
        "explain",
        "diagnose",
        "decide",
        "warn",
        "report",
        "summarize",
    ):
        assert community_language.count(f"<{reader_task}-example-") == 2

    assert "community-language.md" in humanize_skill
    community_language_bytes = len(community_language.encode("utf-8"))
    assert community_language_bytes <= MAXIMUM_COMMUNITY_LANGUAGE_BYTES, (
        "the on-demand example corpus must stay compact; it now costs "
        f"{community_language_bytes} bytes"
    )

    assert not (HOOK_DOMAIN_DIRECTORY / "interactive-communication.md").exists()
    assert not (HOOK_DOMAIN_DIRECTORY / "community-language.md").exists()


def test_no_generated_policy_surface_sits_between_owners_and_consumers():
    assert not [path for path in REMOVED_GENERATED_SURFACES if path.exists()]


def test_hooks_enforce_the_policy_without_rendering_instruction_surfaces():
    catalog = REPLY_RULE_CATALOG_PATH.read_text(encoding="utf-8")
    feedback = REPLY_RULE_FEEDBACK_PATH.read_text(encoding="utf-8")

    assert "instruction_sentence" not in catalog
    assert "applies_to" not in catalog
    assert "interactive-communication.md" not in feedback
    assert "rendered_markdown_surface" not in feedback


def test_humanize_is_the_output_policy_and_artifact_adapter():
    skill_text = HUMANIZE_SKILL_PATH.read_text(encoding="utf-8")
    description = (frontmatter_key_values(skill_text) or {}).get("description", "")

    assert "human-readable output policy" in description.lower()
    assert "interactive hooks route failed replies to it" in description.lower()
    assert "enforced-wording-rules.md" not in skill_text
    assert "employer-identifying" in skill_text
    assert "human-communication-policy.md" not in skill_text
    assert not (HUMANIZE_DIRECTORY / "human-communication-policy.md").exists()
    for superseded_chapter in (
        "channels.md",
        "simplified-technical-english.md",
        "tells.md",
    ):
        assert not (HUMANIZE_DIRECTORY / superseded_chapter).exists()


def test_superseded_split_interactive_surfaces_are_removed():
    assert not (CORE_COMMUNICATION_DIRECTORY / "interactive-preferences.md").exists()
    assert not (CORE_COMMUNICATION_DIRECTORY / "enforced-reply-rules.md").exists()
