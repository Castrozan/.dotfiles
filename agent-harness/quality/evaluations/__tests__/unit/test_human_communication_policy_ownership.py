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
REPLY_RULE_CATALOG_PATH = HOOK_DOMAIN_DIRECTORY / "reply_rule_catalog.py"
REPLY_RULE_FEEDBACK_PATH = HOOK_DOMAIN_DIRECTORY / "reply_rule_feedback.py"

INTERACTIVE_LAUNCHER_EXPECTATIONS = {
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "claude-code"
    / "skill-injection"
    / "interactive-sessions.nix": (
        "humanize/SKILL.md",
        "agent-instructions/skills/humanize/interactive-communication.md",
    ),
    REPO_ROOT / "agent-harness" / "harnesses" / "codex" / "package.nix": (
        "humanize/SKILL.md",
        "agent-instructions/skills/humanize/interactive-communication.md",
    ),
    REPO_ROOT / "agent-harness" / "harnesses" / "opencode" / "opencode.nix": (
        "humanize/SKILL.md",
        "agent-instructions/skills/humanize/interactive-communication.md",
    ),
    REPO_ROOT / "agent-harness" / "harnesses" / "pi" / "package.nix": (
        "humanize/SKILL.md",
        "agent-instructions/skills/humanize/interactive-communication.md",
    ),
}
INTERACTIVE_LAUNCH_SOURCES = (
    *tuple(INTERACTIVE_LAUNCHER_EXPECTATIONS)[:3],
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "pi"
    / "scripts"
    / "launch-pi-with-the-interactive-reply-rules.sh",
)

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
        "interactive-session",
        "humanize-policy-loading",
        "peer-communication",
        "work-in-progress-updates",
        "artifact-links",
        "exhaust-before-returning",
        "reply_template",
        "always_enforced",
        "request_gated",
    ):
        assert f"<{tag}>" in interactive_policy

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

    assert not (HOOK_DOMAIN_DIRECTORY / "interactive-communication.md").exists()


def test_each_harness_composes_the_canonical_units_directly():
    for launcher_path, expected_sources in INTERACTIVE_LAUNCHER_EXPECTATIONS.items():
        launcher = launcher_path.read_text(encoding="utf-8")
        for expected_source in expected_sources:
            assert expected_source in launcher
        assert "interactive-human-communication.md" not in launcher
        assert "interactive-hook-communication.md" not in launcher


def test_each_harness_marks_the_same_interactive_session_boundary():
    for launcher_path in INTERACTIVE_LAUNCH_SOURCES:
        assert "AGENT_INTERACTIVE_PREFERENCES_PATH" in launcher_path.read_text(
            encoding="utf-8"
        )


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
    assert "interactive hooks require it" in description.lower()
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
