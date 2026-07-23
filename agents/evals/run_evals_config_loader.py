from pathlib import Path

import yaml

from run_evals_worktree_and_environment import REPO_ROOT


def load_skill_body_from_path(skill_path: Path) -> str | None:
    if not skill_path.exists():
        return None
    content = skill_path.read_text()
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return content.strip()


def resolve_system_prompt_for_test(test: dict) -> str | None:
    if "system_prompt" in test:
        return test["system_prompt"]

    skill_path_value = test.get("skill_path")
    if not skill_path_value:
        agent_name = test.get("agent")
        if agent_name:
            skill_path_value = f"agents/skills/{agent_name}/SKILL.md"
        else:
            return None

    resolved_path = REPO_ROOT / skill_path_value
    primary_body = load_skill_body_from_path(resolved_path)
    if primary_body is None:
        return None

    extra_skill_path_values = test.get("extra_skill_paths") or []
    extra_bodies = []
    for extra_skill_path_value in extra_skill_path_values:
        extra_resolved_path = REPO_ROOT / extra_skill_path_value
        extra_body = load_skill_body_from_path(extra_resolved_path)
        if extra_body:
            extra_bodies.append(extra_body)

    if not extra_bodies:
        return primary_body
    return primary_body + "\n\n" + "\n\n".join(extra_bodies)


def discover_skill_adjacent_eval_files(repo_root: Path) -> dict[str, list[dict]]:
    discovered_tests = {}
    for yaml_file in sorted(repo_root.glob("agents/skills/*/__tests__/evals/*.yaml")):
        if yaml_file.name == "settings.yaml":
            continue
        skill_name = yaml_file.parent.parent.name
        category_name = f"skills/{skill_name}/{yaml_file.stem}"
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            if data and "tests" in data:
                discovered_tests[category_name] = data["tests"]
    return discovered_tests


def load_config(config_path: Path) -> dict:
    if config_path.is_dir():
        return load_config_from_dir(config_path)
    with open(config_path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return {"settings": {}, "tests": {}}
    if isinstance(data.get("tests"), list):
        data["tests"] = {config_path.stem: data["tests"]}
    return data


def load_config_from_dir(config_dir: Path) -> dict:
    config = {"settings": {}, "tests": {}, "smoke_test": None}

    settings_file = config_dir / "settings.yaml"
    if settings_file.exists():
        with open(settings_file) as f:
            data = yaml.safe_load(f)
            config["settings"] = data.get("settings", {})
            if "smoke_test" in data:
                config["smoke_test"] = data["smoke_test"]

    for yaml_file in sorted(config_dir.glob("*.yaml")):
        if yaml_file.name == "settings.yaml":
            continue
        category_name = yaml_file.stem
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            if data and "tests" in data:
                config["tests"][category_name] = data["tests"]

    skill_adjacent_tests = discover_skill_adjacent_eval_files(REPO_ROOT)
    config["tests"].update(skill_adjacent_tests)

    return config
