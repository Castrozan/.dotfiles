import re

from instruction_surface_scanner import REPO_ROOT


INSTRUCTION_ROOT = REPO_ROOT / "agent-harness" / "agent-instructions"
CLAUDE_MD_GUIDANCE_PATH = (
    INSTRUCTION_ROOT / "skills" / "instructions" / "references" / "claude-md.md"
)
HERDR_SKILL_PATH = INSTRUCTION_ROOT / "skills" / "herdr" / "SKILL.md"
NIX_EXPERT_PATH = INSTRUCTION_ROOT / "skills" / "nix" / "references" / "expert.md"
ORCHESTRATE_SKILL_PATH = INSTRUCTION_ROOT / "skills" / "orchestrate" / "SKILL.md"
REVIEW_AUTHORING_PATH = (
    INSTRUCTION_ROOT / "skills" / "review" / "references" / "authoring.md"
)


def normalized_text(path):
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def test_instruction_authoring_guidance_uses_core_scope_and_horizon():
    claude_md_guidance = normalized_text(CLAUDE_MD_GUIDANCE_PATH)
    authoring_review = normalized_text(REVIEW_AUTHORING_PATH)

    assert "<instruction_placement>" in claude_md_guidance
    assert "<instruction_placement>" in authoring_review
    assert "Everything else either belongs in a skill" not in claude_md_guidance
    assert "Policy that must apply every session belongs in CLAUDE.md" not in (
        authoring_review
    )


def test_nix_expert_defers_persistent_coding_and_repository_verification():
    nix_expert = normalized_text(NIX_EXPERT_PATH)

    assert "<coding>" in nix_expert
    assert "never code comments" not in nix_expert
    assert "nix flake check and nix build" not in nix_expert
    assert "`references/repo.md`" in nix_expert
    assert "`references/rebuild.md`" in nix_expert


def test_a2a_messages_carry_claimed_sender_identity():
    orchestrate = normalized_text(ORCHESTRATE_SKILL_PATH)

    for required_contract in (
        "every message dispatched through a2a",
        "sender's current Servant name",
        "claimed identity",
        "does not authenticate",
    ):
        assert required_contract in orchestrate


def test_agents_close_the_herdr_panes_they_create():
    herdr = normalized_text(HERDR_SKILL_PATH)
    orchestrate = normalized_text(ORCHESTRATE_SKILL_PATH)

    for required_contract in (
        "Close every pane or tab you create",
        "user explicitly asks to preserve or take over that session",
        "never close a pre-existing pane",
    ):
        assert required_contract in herdr

    assert "owned-pane cleanup rule" in orchestrate
    assert "leaving its pane in place for the human to close" not in orchestrate
