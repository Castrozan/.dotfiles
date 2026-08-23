import re

from instruction_surface_scanner import REPO_ROOT


INSTRUCTION_ROOT = REPO_ROOT / "agent-harness" / "agent-instructions"
CLAUDE_MD_GUIDANCE_PATH = INSTRUCTION_ROOT / "skills" / "instructions" / "claude-md.md"
NIX_EXPERT_PATH = INSTRUCTION_ROOT / "skills" / "nix" / "expert.md"
ORCHESTRATE_SKILL_PATH = INSTRUCTION_ROOT / "skills" / "orchestrate" / "SKILL.md"
REVIEW_AUTHORING_PATH = INSTRUCTION_ROOT / "skills" / "review" / "authoring.md"


def normalized_text(path):
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def test_instruction_authoring_guidance_uses_core_scope_and_horizon():
    claude_md_guidance = normalized_text(CLAUDE_MD_GUIDANCE_PATH)
    authoring_review = normalized_text(REVIEW_AUTHORING_PATH)

    assert "<instruction-placement>" in claude_md_guidance
    assert "<instruction-placement>" in authoring_review
    assert "Everything else either belongs in a skill" not in claude_md_guidance
    assert "Policy that must apply every session belongs in CLAUDE.md" not in (
        authoring_review
    )


def test_nix_expert_defers_persistent_coding_and_repository_verification():
    nix_expert = normalized_text(NIX_EXPERT_PATH)

    assert "<coding>" in nix_expert
    assert "never code comments" not in nix_expert
    assert "nix flake check and nix build" not in nix_expert
    assert "`repo.md`" in nix_expert
    assert "`rebuild.md`" in nix_expert


def test_a2a_messages_carry_claimed_sender_identity():
    orchestrate = normalized_text(ORCHESTRATE_SKILL_PATH)

    for required_contract in (
        "every message dispatched through a2a",
        "sender's current Servant name",
        "claimed identity",
        "does not authenticate",
    ):
        assert required_contract in orchestrate
