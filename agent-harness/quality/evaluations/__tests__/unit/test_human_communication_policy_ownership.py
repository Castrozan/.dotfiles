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
INTERACTIVE_POLICY_PATH = (
    HUMANIZE_DIRECTORY / "references" / "interactive-communication.md"
)
REPLY_RULE_CATALOG_PATH = HOOK_DOMAIN_DIRECTORY / "reply_rule_catalog.py"
REPLY_RULE_FEEDBACK_PATH = HOOK_DOMAIN_DIRECTORY / "reply_rule_feedback.py"
MAXIMUM_HUMANIZE_SKILL_BYTES = 15000

REMOVED_GENERATED_SURFACES = (
    CORE_COMMUNICATION_DIRECTORY / "interactive-human-communication.md",
    CORE_COMMUNICATION_DIRECTORY / "interactive-hook-communication.md",
    HUMANIZE_DIRECTORY / "enforced-wording-rules.md",
    CORE_COMMUNICATION_DIRECTORY / "render-human-communication-markdown.py",
)


def test_humanize_package_owns_interactive_and_output_policies():
    interactive_policy = INTERACTIVE_POLICY_PATH.read_text(encoding="utf-8")
    humanize_skill = HUMANIZE_SKILL_PATH.read_text(encoding="utf-8")

    for tag in (
        "interactive_session",
        "humanize_policy_loading",
        "peer_communication",
        "work_in_progress_updates",
        "artifact_links",
        "exhaust_before_returning",
        "response_shape",
        "concise_request",
    ):
        assert f"<{tag}>" in interactive_policy

    for tag in (
        "reader_understanding_policy",
        "source_fidelity",
        "whole_context_cohesion",
        "representation_selection",
        "representation_rendering",
        "meaning_and_certainty",
        "confusion_recovery",
        "terminology_and_jargon",
        "sentence_and_paragraph_construction",
        "procedures_and_explanations",
        "human_register",
        "revision_and_semantic_check",
        "durable_artifacts",
    ):
        assert f"<{tag}>" in humanize_skill

    for removed_tag in (
        "controlled-language-application",
        "supplied-fact-precedence",
        "task-and-reader-model",
        "procedures-explanations-and-warnings",
        "controlled-language-adaptation",
        "human-facing-channel-rules",
        "durable-report-rules",
    ):
        assert f"<{removed_tag}>" not in humanize_skill

    humanize_skill_bytes = len(humanize_skill.encode("utf-8"))
    assert humanize_skill_bytes <= MAXIMUM_HUMANIZE_SKILL_BYTES, (
        "the on-demand Humanize skill must stay compact; it now costs "
        f"{humanize_skill_bytes} bytes"
    )

    assert not (HOOK_DOMAIN_DIRECTORY / "interactive-communication.md").exists()


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

    normalized_description = description.lower()
    assert "substantial human-facing" in normalized_description
    assert "one- or two-sentence confirmations" in normalized_description
    assert "enforced-wording-rules.md" not in skill_text
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


def test_humanize_explains_unresolved_choices_before_internal_rationale():
    skill_text = HUMANIZE_SKILL_PATH.read_text(encoding="utf-8").lower()

    for required_behavior in (
        "who acts",
        "what changes",
        "scope",
        "what remains unchanged",
        "before internal rationale",
    ):
        assert required_behavior in skill_text


def test_humanize_uses_established_language_before_coining_terms():
    skill_text = HUMANIZE_SKILL_PATH.read_text(encoding="utf-8").lower()

    for required_behavior in (
        "ubiquitous language",
        "context already uses",
        "before coining a new term",
        "term the reader has rejected",
    ):
        assert required_behavior in skill_text


def test_humanize_integrates_new_information_without_recency_priority():
    skill_text = " ".join(
        HUMANIZE_SKILL_PATH.read_text(encoding="utf-8").lower().split()
    )

    for required_behavior in (
        "because it is recent",
        "full context",
        "restructure the whole piece",
        "cohesive",
    ):
        assert required_behavior in skill_text
