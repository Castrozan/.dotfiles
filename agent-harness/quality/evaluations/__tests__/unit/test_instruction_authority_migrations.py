import re

from instruction_surface_scanner import REPO_ROOT


AGENT_HARNESS_SKILL_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "agent-harness"
    / "SKILL.md"
)
AUTHORITY_RECIPE_PATH = (
    AGENT_HARNESS_SKILL_PATH.parent / "references" / "instruction-authority.md"
)
CORE_COMPLEMENT_REQUIREMENTS = {
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "core-rules"
    / "adaptive-implementation-delivery-process.md": ("<delegation>",),
    AGENT_HARNESS_SKILL_PATH: ("<evidence>", "<completion>", "<coding>"),
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "deep-work"
    / "SKILL.md": ("<context>",),
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "deliver"
    / "SKILL.md": (
        "<evidence>",
        "<autonomy>",
        "<completion>",
        "<delegation>",
        "<context>",
        "<coding>",
    ),
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "explore"
    / "SKILL.md": ("<evidence>",),
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "humanize"
    / "SKILL.md": ("<evidence>", "<autonomy>"),
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "humanize"
    / "references"
    / "interactive-communication.md": (
        "<evidence>",
        "<autonomy>",
        "<completion>",
    ),
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "orchestrate"
    / "SKILL.md": ("<delegation>", "<completion>"),
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "research"
    / "SKILL.md": ("<evidence>", "<autonomy>"),
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "review"
    / "SKILL.md": ("<evidence>", "<completion>", "<coding>"),
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "instructions"
    / "references"
    / "subagent-briefs.md": ("<delegation>",),
}
HUMANIZE_INTERACTIVE_PATH = (
    REPO_ROOT
    / "agent-harness"
    / "agent-instructions"
    / "skills"
    / "humanize"
    / "references"
    / "interactive-communication.md"
)
HERMES_DIRECTORY = REPO_ROOT / "agent-harness" / "harnesses" / "hermes"


def normalized_text(path):
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def test_agent_harness_routes_instruction_authority_diagnosis_to_one_recipe():
    skill = AGENT_HARNESS_SKILL_PATH.read_text(encoding="utf-8")
    recipe = AUTHORITY_RECIPE_PATH.read_text(encoding="utf-8")

    assert "`references/instruction-authority.md`" in skill
    for section in (
        "behavior_contract",
        "runtime_trace",
        "owner_selection",
        "relationship_classification",
        "migration",
        "verification",
    ):
        assert f"<{section}>" in recipe

    for required_distinction in (
        "trigger, action, material exceptions",
        "generated copy",
        "runtime injection",
        "deterministic control",
        "ordinary request",
    ):
        assert required_distinction in normalized_text(AUTHORITY_RECIPE_PATH)


def test_every_migrated_complement_points_to_its_core_authority():
    missing_links = {
        str(path.relative_to(REPO_ROOT)): [
            authority
            for authority in authorities
            if authority not in path.read_text(encoding="utf-8")
        ]
        for path, authorities in CORE_COMPLEMENT_REQUIREMENTS.items()
        if any(
            authority not in path.read_text(encoding="utf-8")
            for authority in authorities
        )
    }

    assert not missing_links


def test_humanize_does_not_restate_general_core_decision_thresholds():
    interactive_policy = normalized_text(HUMANIZE_INTERACTIVE_PATH)

    for retired_duplicate in (
        "When challenged, verify the relevant evidence before defending or retracting",
        "Ask only when an unresolved choice would materially change the outcome",
        "Return only when the task is done",
    ):
        assert retired_duplicate not in interactive_policy


def test_hermes_declares_managed_core_and_removes_memory_authority():
    soul_source = (HERMES_DIRECTORY / "soul.nix").read_text(encoding="utf-8")
    config_source = (HERMES_DIRECTORY / "config.nix").read_text(encoding="utf-8")
    launcher_source = (HERMES_DIRECTORY / "scripts" / "hermes-launch").read_text(
        encoding="utf-8"
    )
    migration_source = (HERMES_DIRECTORY / "migration.nix").read_text(encoding="utf-8")
    managed_memory_source = migration_source.split("retiredUserMemoryEntryPrefixes", 1)[
        0
    ]

    assert "agent-instructions/core-rules/core.md" in soul_source
    assert (
        "agent-instructions/skills/humanize/references/interactive-communication.md"
        in (config_source)
    )
    for managed_surface in (
        "HERMES_AGENT_SOUL",
        "HERMES_AGENT_HUMANIZE_SKILL",
        "HERMES_AGENT_DOCS_SKILL",
        "HERMES_AGENT_MEMORY_SYNCHRONIZER",
    ):
        assert managed_surface in launcher_source

    for retired_memory_authority in (
        "Correction stance:",
        "Uncertainty:",
        "Interactive reply shape:",
        "Before returning control:",
        "Code style he enforces:",
        "Scripts:",
        "Git:",
    ):
        assert retired_memory_authority not in managed_memory_source

    assert "keeps its own OAuth session in ~/.hermes/auth.json" in (
        managed_memory_source
    )
    assert "seeds access" not in managed_memory_source
