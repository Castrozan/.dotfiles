from instruction_surface_scanner import (
    REPO_ROOT,
    frontmatter_key_values,
    skill_definition_files,
)

MAXIMUM_ALWAYS_ON_INSTRUCTION_BYTES = 34000
MAXIMUM_ALWAYS_ON_SKILL_DESCRIPTION_BYTES = 12000


def always_on_instruction_files():
    return sorted(
        (REPO_ROOT / "agent-harness" / "agent-instructions" / "core-rules").glob(
            "**/*.md"
        )
    ) + [
        REPO_ROOT
        / "agent-harness"
        / "agent-instructions"
        / "project-context"
        / "dotfiles-agent-instructions.md"
    ]


def always_on_instruction_bytes():
    return sum(len(path.read_bytes()) for path in always_on_instruction_files())


def always_on_skill_description_bytes():
    return sum(
        len((frontmatter_key_values(path.read_text()) or {}).get("description", ""))
        for path in skill_definition_files()
    )


def test_the_always_on_instruction_surface_stays_within_its_budget():
    total = always_on_instruction_bytes()
    assert total <= MAXIMUM_ALWAYS_ON_INSTRUCTION_BYTES, (
        f"core rules plus project-context instructions now cost {total} bytes of every "
        f"session's context, past the {MAXIMUM_ALWAYS_ON_INSTRUCTION_BYTES} byte "
        f"budget. Remove duplication or narrow material by scope and horizon: keep "
        f"universal session-long defaults in core, local policy local, bounded procedures "
        f"in skills, and precise predicates in enforcement rather than raising this ceiling."
    )


def test_the_always_on_skill_descriptions_stay_within_their_budget():
    total = always_on_skill_description_bytes()
    assert total <= MAXIMUM_ALWAYS_ON_SKILL_DESCRIPTION_BYTES, (
        f"skill descriptions now cost {total} bytes of every session's context, past "
        f"the {MAXIMUM_ALWAYS_ON_SKILL_DESCRIPTION_BYTES} byte budget. Every skill "
        f"description is loaded eagerly so the model can route, so tighten the "
        f"descriptions or retire a skill rather than raising this ceiling."
    )


def test_the_harness_auto_memory_stays_disabled():
    declared = (
        REPO_ROOT
        / "agent-harness"
        / "harnesses"
        / "claude-code"
        / "settings"
        / "environment-variables.nix"
    ).read_text()
    assert 'CLAUDE_CODE_DISABLE_AUTO_MEMORY = "1"' in declared, (
        "the harness auto-memory writes per-working-directory stores and loads a "
        "per-fact index into every session at start, which grows without bound and is "
        "never reviewed. Durable facts belong in the skill that owns their domain. "
        "See agent-harness/harnesses/claude-code/docs/agent-memory.md before re-enabling it."
    )


def test_the_budget_check_inspects_a_real_corpus():
    assert len(always_on_instruction_files()) > 3
    assert always_on_instruction_bytes() > 10000
    assert always_on_skill_description_bytes() > 5000
