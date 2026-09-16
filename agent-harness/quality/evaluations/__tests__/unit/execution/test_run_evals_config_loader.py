from runner import run_evals_config_loader
import pytest
from instructions.instruction_surface_scanner import public_skill_definition_path
from runner.run_evals_config_loader import (
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


def test_grouped_skill_keeps_its_eval_category_and_system_prompt(tmp_path, monkeypatch):
    _write_skill_eval(tmp_path, "services/nix", "compliance", "nix_case")
    _write_skill_eval(tmp_path, "workstation/browser", "compliance", "browser_case")
    skill_path = (
        tmp_path / "agent-harness/agent-instructions/skills/services/nix/SKILL.md"
    )
    skill_path.write_text("---\nname: nix\n---\nApply the declared configuration.")
    monkeypatch.setattr(run_evals_config_loader, "REPO_ROOT", tmp_path)

    assert (
        resolve_system_prompt_for_test({"agent": "nix"})
        == "Apply the declared configuration."
    )
    assert (
        discover_skill_adjacent_eval_files(tmp_path)["skills/nix/compliance"][0]["name"]
        == "nix_case"
    )
    assert public_skill_definition_path("missing", tmp_path) is None
    assert list(discover_skill_adjacent_eval_files(tmp_path)) == [
        "skills/browser/compliance",
        "skills/nix/compliance",
    ]


def test_duplicate_public_skill_names_fail_instead_of_selecting_one(tmp_path):
    root = tmp_path / "agent-harness/agent-instructions/skills"
    for group in ("development", "services"):
        path = root / group / "nix" / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text("Configure Nix.")

    with pytest.raises(ValueError, match="Duplicate public skill name: nix"):
        public_skill_definition_path("nix", tmp_path)


def test_system_prompt_can_resolve_instruction_files_from_a_git_ref(monkeypatch):
    monkeypatch.setattr(
        run_evals_config_loader,
        "load_skill_body_from_git_ref",
        lambda path, ref: f"{ref}:{path}",
    )

    prompt = resolve_system_prompt_for_test(
        {
            "skill_path": "agent-harness/agent-instructions/skills/writing/humanize/SKILL.md",
            "extra_skill_paths": [
                "agent-harness/agent-instructions/skills/writing/humanize/references/interactive-communication.md"
            ],
        },
        instruction_ref="b13f3ebb",
    )

    assert (
        "b13f3ebb:agent-harness/agent-instructions/skills/writing/humanize/SKILL.md"
        in prompt
    )
    assert (
        "b13f3ebb:agent-harness/agent-instructions/skills/writing/humanize/references/interactive-communication.md"
        in prompt
    )
