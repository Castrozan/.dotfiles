import re

from instruction_surface_scanner import REPO_ROOT, frontmatter_key_values


HOOK_DOMAIN_DIRECTORY = (
    REPO_ROOT / "agent-harness" / "hooks" / "runtime" / "common" / "human_facing_reply"
)
INTERACTIVE_POLICY_PATH = HOOK_DOMAIN_DIRECTORY / "interactive-communication.md"
CORE_COMMUNICATION_DIRECTORY = (
    REPO_ROOT / "agent-harness" / "agent-instructions" / "core-rules" / "communication"
)
FULL_INTERACTIVE_SURFACE_PATH = (
    CORE_COMMUNICATION_DIRECTORY / "interactive-human-communication.md"
)
HOOK_INTERACTIVE_SURFACE_PATH = (
    CORE_COMMUNICATION_DIRECTORY / "interactive-hook-communication.md"
)
HUMANIZE_DIRECTORY = (
    REPO_ROOT / "agent-harness" / "agent-instructions" / "skills" / "humanize"
)
HUMANIZE_SKILL_PATH = HUMANIZE_DIRECTORY / "SKILL.md"

INTERACTIVE_LAUNCHER_EXPECTATIONS = {
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "claude-code"
    / "skill-injection"
    / "interactive-sessions.nix": "interactive-hook-communication.md",
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "codex"
    / "package.nix": "interactive-human-communication.md",
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "opencode"
    / "opencode.nix": "interactive-human-communication.md",
    REPO_ROOT
    / "agent-harness"
    / "harnesses"
    / "pi"
    / "package.nix": "interactive-human-communication.md",
}


def tagged_section(text: str, tag: str) -> str:
    matched = re.search(rf"<{tag}>.*?</{tag}>", text, re.DOTALL)
    assert matched, f"missing <{tag}> section"
    return matched.group(0)


def test_hook_and_skill_own_separate_interactive_and_output_policies():
    interactive_policy = INTERACTIVE_POLICY_PATH.read_text(encoding="utf-8")
    humanize_skill = HUMANIZE_SKILL_PATH.read_text(encoding="utf-8")

    for tag in (
        "interactive-session",
        "humanize-skill-gate",
        "peer-communication",
        "work-in-progress-updates",
        "artifact-links",
        "exhaust-before-returning",
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
    ):
        assert f"<{tag}>" in humanize_skill


def test_each_harness_loads_the_surface_supported_by_its_skill_tooling():
    for launcher_path, expected_surface in INTERACTIVE_LAUNCHER_EXPECTATIONS.items():
        launcher = launcher_path.read_text(encoding="utf-8")
        assert expected_surface in launcher
        assert "interactive-preferences.md" not in launcher
        assert "enforced-reply-rules.md" not in launcher


def test_generated_surfaces_compose_their_authoritative_sources():
    humanize_skill = HUMANIZE_SKILL_PATH.read_text(encoding="utf-8")
    shared_output_policy = tagged_section(humanize_skill, "human-readable-output")
    interactive_policy = INTERACTIVE_POLICY_PATH.read_text(encoding="utf-8").strip()
    full_surface = FULL_INTERACTIVE_SURFACE_PATH.read_text(encoding="utf-8")
    hook_surface = HOOK_INTERACTIVE_SURFACE_PATH.read_text(encoding="utf-8")

    assert full_surface.startswith(shared_output_policy)
    assert interactive_policy in full_surface
    assert hook_surface.startswith(interactive_policy)
    for surface in (full_surface, hook_surface):
        assert "<reply_template>" in surface
        assert "<always_enforced>" in surface
        assert "<request_gated>" in surface


def test_humanize_is_the_output_policy_and_artifact_adapter():
    skill_text = HUMANIZE_SKILL_PATH.read_text(encoding="utf-8")
    description = (frontmatter_key_values(skill_text) or {}).get("description", "")

    assert "human-readable output policy" in description.lower()
    assert "interactive hooks require it" in description.lower()
    assert "enforced-wording-rules.md" in skill_text
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
