import run_evals_config_loader
from run_evals_config_loader import (
    discover_skill_adjacent_eval_files,
    resolve_system_prompt_for_test,
)


def _write_skill_eval(repo_root, skill, stem, test_name):
    eval_dir = (
        repo_root
        / "agent-harness"
        / "agent-instructions"
        / "skills"
        / skill
        / "__tests__"
        / "evals"
    )
    eval_dir.mkdir(parents=True, exist_ok=True)
    (eval_dir / f"{stem}.yaml").write_text(
        f"tests:\n  - name: {test_name}\n    prompt: p\n"
    )


def test_discovery_keeps_same_stem_evals_from_different_skills(tmp_path):
    _write_skill_eval(tmp_path, "git", "compliance", "git_case")
    _write_skill_eval(tmp_path, "nix", "compliance", "nix_case")

    discovered = discover_skill_adjacent_eval_files(tmp_path)

    assert "skills/git/compliance" in discovered
    assert "skills/nix/compliance" in discovered
    assert discovered["skills/git/compliance"][0]["name"] == "git_case"
    assert discovered["skills/nix/compliance"][0]["name"] == "nix_case"


def test_system_prompt_can_resolve_instruction_files_from_a_git_ref(monkeypatch):
    monkeypatch.setattr(
        run_evals_config_loader,
        "load_skill_body_from_git_ref",
        lambda path, ref: f"{ref}:{path}",
    )

    prompt = resolve_system_prompt_for_test(
        {
            "skill_path": "agent-harness/agent-instructions/skills/humanize/SKILL.md",
            "extra_skill_paths": [
                "agent-harness/agent-instructions/skills/humanize/interactive-communication.md"
            ],
        },
        instruction_ref="b13f3ebb",
    )

    assert (
        "b13f3ebb:agent-harness/agent-instructions/skills/humanize/SKILL.md" in prompt
    )
    assert (
        "b13f3ebb:agent-harness/agent-instructions/skills/humanize/interactive-communication.md"
        in prompt
    )
