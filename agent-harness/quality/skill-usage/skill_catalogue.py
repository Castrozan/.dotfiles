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


def measured_cases(suite: dict) -> list[dict]:
    return [case for case in suite.get("casos", []) if not case.get("pendente")]


def routing_case_counts(suites: list[dict]) -> Counter:
    return Counter(
        expected_skill
        for suite in suites
        if suite.get("categoria") == ROUTING_CATEGORY
        for case in measured_cases(suite)
        for expected_skill in (case.get("assercoes") or {}).get("igual", [])
    )


def skill_case_counts(suites: list[dict]) -> Counter:
    counts: Counter = Counter()
    for suite in suites:
        category = str(suite.get("categoria", ""))
        if category.startswith(SKILL_SUITE_CATEGORY_PREFIX):
            counts[category.split("/")[1]] += len(measured_cases(suite))
    return counts


def evaluation_coverage(repository: Path) -> EvaluationCoverage:
    suites = evaluation_suites(repository)
    return EvaluationCoverage(routing_case_counts(suites), skill_case_counts(suites))
