from run_evals_config_loader import discover_skill_adjacent_eval_files


def _write_skill_eval(repo_root, skill, stem, test_name):
    eval_dir = repo_root / "agents" / "skills" / skill / "__tests__" / "evals"
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
