from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import yaml

EVALUATION_CONFIGURATION = Path("agent-harness/quality/evaluations/config.yaml")
ROUTING_CATEGORY = "skill_routing"
SKILL_SUITE_CATEGORY_PREFIX = "skills/"


@dataclass(frozen=True)
class InstalledSkill:
    name: str
    tier: str
    instruction_characters: int


@dataclass(frozen=True)
class EvaluationCoverage:
    routing_cases: Counter
    skill_cases: Counter


def skills_under(skills_directory: Path, tier: str) -> list[InstalledSkill]:
    if not skills_directory.is_dir():
        return []
    return [
        InstalledSkill(
            skill_file.parent.name, tier, len(skill_file.read_text(errors="replace"))
        )
        for skill_file in sorted(skills_directory.glob("*/SKILL.md"))
    ]


def installed_skills(plugin_root: Path) -> dict[str, InstalledSkill]:
    return {
        skill.name: skill
        for skills_directory, tier in (
            (plugin_root / "library" / "skills", "library"),
            (plugin_root / "skills", "top"),
        )
        for skill in skills_under(skills_directory, tier)
    }


def evaluation_suites(repository: Path) -> list[dict]:
    configuration_path = repository / EVALUATION_CONFIGURATION
    if not configuration_path.is_file():
        return []
    configuration = yaml.safe_load(configuration_path.read_text())
    return [
        yaml.safe_load(suite_path.read_text())
        for pattern in configuration.get("casos", [])
        for suite_path in sorted(repository.glob(pattern))
    ]


def evaluation_coverage(repository: Path) -> EvaluationCoverage:
    routing_cases: Counter = Counter()
    skill_cases: Counter = Counter()
    for suite in evaluation_suites(repository):
        category = str(suite.get("categoria", ""))
        measured_cases = [
            case for case in suite.get("casos", []) if not case.get("pendente")
        ]
        if category == ROUTING_CATEGORY:
            for case in measured_cases:
                for expected_skill in (case.get("assercoes") or {}).get("igual", []):
                    routing_cases[expected_skill] += 1
        elif category.startswith(SKILL_SUITE_CATEGORY_PREFIX):
            skill_cases[category.split("/")[1]] += len(measured_cases)
    return EvaluationCoverage(routing_cases, skill_cases)
