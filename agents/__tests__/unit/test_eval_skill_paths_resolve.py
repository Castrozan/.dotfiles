from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
EVAL_CONFIG_DIR = REPO_ROOT / "agents" / "evals" / "config"


def collect_referenced_skill_paths():
    referenced = []
    eval_files = sorted(EVAL_CONFIG_DIR.glob("*.yaml")) + sorted(
        REPO_ROOT.glob("agents/skills/*/__tests__/evals/*.yaml")
    )
    for eval_file in eval_files:
        if eval_file.name == "settings.yaml":
            continue
        data = yaml.safe_load(eval_file.read_text())
        if not data or "tests" not in data:
            continue
        for test in data["tests"]:
            candidates = [test.get("skill_path")]
            candidates.extend(test.get("extra_skill_paths") or [])
            for candidate in candidates:
                if candidate:
                    referenced.append((eval_file, test["name"], candidate))
    return referenced


def test_every_eval_skill_path_resolves_to_a_file_in_the_repo():
    unresolved = [
        f"{eval_file.relative_to(REPO_ROOT)}:{test_name} -> {candidate}"
        for eval_file, test_name, candidate in collect_referenced_skill_paths()
        if not (REPO_ROOT / candidate).is_file()
    ]
    assert not unresolved, (
        "these eval skill_path entries point at files that no longer exist, so the "
        "runner silently injects no system prompt and the test grades ambient "
        "context instead of the rule: " + ", ".join(unresolved)
    )


def test_the_skill_path_scan_covers_the_eval_suites():
    assert len(collect_referenced_skill_paths()) > 50
