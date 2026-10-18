from instructions.instruction_surface_scanner import REPO_ROOT, frontmatter_key_values


HOOK_DOMAIN_DIRECTORY = (
    REPO_ROOT / "agent-harness" / "hooks" / "runtime" / "common" / "human_facing_reply"
)
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
INTERACTIVE_POLICY_PATH = (
    HUMANIZE_DIRECTORY / "references" / "interactive-communication.md"
)
REPLY_RULE_CATALOG_PATH = HOOK_DOMAIN_DIRECTORY / "reply_rule_catalog.py"
REPLY_RULE_FEEDBACK_PATH = HOOK_DOMAIN_DIRECTORY / "reply_rule_feedback.py"
MAXIMUM_HUMANIZE_SKILL_BYTES = 4000

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
        "humanize_policy_loading",
        "peer_communication",
        "work_in_progress_updates",
        "artifact_links",
        "exhaust_before_returning",
        "response_shape",
    ):
        assert "### " + tag.replace("_", " ").capitalize() in interactive_policy

    for tag in (
        "reader_understanding_policy",
        "source_fidelity",
        "representation_selection",
        "confusion_recovery",
        "procedures_and_explanations",
        "human_register",
    ):
        assert "### " + tag.replace("_", " ").capitalize() in humanize_skill

    for removed_tag in (
        "controlled-language-application",
        "supplied-fact-precedence",
        "task-and-reader-model",
        "procedures-explanations-and-warnings",
        "controlled-language-adaptation",
        "human-facing-channel-rules",
        "durable-report-rules",
    ):
        assert "### " + removed_tag.replace("_", " ").capitalize() not in humanize_skill

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


def test_humanize_owns_session_replies_and_excludes_file_authoring():
    skill_text = HUMANIZE_SKILL_PATH.read_text(encoding="utf-8")
    description = (frontmatter_key_values(skill_text) or {}).get("description", "")

    normalized_description = description.lower()
    assert "active agent sessions" in normalized_description
    assert "substantial replies" in normalized_description
    assert "file authoring" in normalized_description
    assert "### Durable artifacts" not in skill_text
    assert "Use the `docs` skill" not in skill_text
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
    skill_text = " ".join(
        HUMANIZE_SKILL_PATH.read_text(encoding="utf-8").lower().split()
    )

    for required_behavior in (
        "who acts",
        "what changes",
        "scope",
        "material tradeoffs",
        "before internal rationale",
    ):
        assert required_behavior in skill_text


def test_humanize_uses_established_language_before_coining_terms():
    skill_text = " ".join(
        HUMANIZE_SKILL_PATH.read_text(encoding="utf-8").lower().split()
    )

    for required_behavior in (
        "established terms consistently",
        "concrete referents",
        "reader's terms",
    ):
        assert required_behavior in skill_text


def test_humanize_integrates_new_information_without_recency_priority():
    skill_text = " ".join(
        HUMANIZE_SKILL_PATH.read_text(encoding="utf-8").lower().split()
    )

    for required_behavior in ("full session",):
        assert required_behavior in skill_text
