from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_catalogue import (  # noqa: E402
    EvaluationCoverage,
    InstalledSkill,
    evaluation_coverage,
    installed_skills,
)
from skill_load_events import SkillLoad, skill_loads  # noqa: E402

CHANNELS = ("agent", "typed", "pinned", "nested")
COLUMNS = (
    "skill",
    "tier",
    *CHANNELS,
    "sessions",
    "last",
    "routing",
    "evals",
    "chars",
)


@dataclass
class SkillUsage:
    loads_by_channel: Counter = field(default_factory=Counter)
    sessions: set = field(default_factory=set)
    last_loaded: datetime | None = None

    def record(self, load: SkillLoad) -> None:
        self.loads_by_channel[load.channel] += 1
        self.sessions.add(load.session_identifier)
        if self.last_loaded is None or load.timestamp > self.last_loaded:
            self.last_loaded = load.timestamp

    @property
    def total_loads(self) -> int:
        return sum(self.loads_by_channel.values())


def usage_by_skill(
    loads, catalogue: dict[str, InstalledSkill]
) -> dict[str, SkillUsage]:
    usage: dict[str, SkillUsage] = defaultdict(SkillUsage)
    for load in loads:
        if load.skill in catalogue:
            usage[load.skill].record(load)
    return usage


def ranked_skill_names(
    catalogue: dict[str, InstalledSkill], usage: dict[str, SkillUsage]
) -> list[str]:
    return sorted(
        catalogue, key=lambda name: (-usage.get(name, SkillUsage()).total_loads, name)
    )


def report_rows(
    catalogue: dict[str, InstalledSkill],
    usage: dict[str, SkillUsage],
    coverage: EvaluationCoverage,
) -> list[tuple[str, ...]]:
    rows = []
    for name in ranked_skill_names(catalogue, usage):
        skill_usage = usage.get(name, SkillUsage())
        rows.append(
            (
                name,
                catalogue[name].tier,
                *(str(skill_usage.loads_by_channel[channel]) for channel in CHANNELS),
                str(len(skill_usage.sessions)),
                skill_usage.last_loaded.date().isoformat()
                if skill_usage.last_loaded
                else "-",
                str(coverage.routing_cases[name]),
                str(coverage.skill_cases[name]),
                str(catalogue[name].instruction_characters),
            )
        )
    return rows


def aligned_table(rows: list[tuple[str, ...]]) -> str:
    widths = [
        max(len(row[index]) for row in [COLUMNS, *rows])
        for index in range(len(COLUMNS))
    ]
    return "\n".join(
        "  ".join(
            cell.ljust(width) for cell, width in zip(row, widths, strict=True)
        ).rstrip()
        for row in [COLUMNS, *rows]
    )


def is_agent_chosen_without_eval_case(
    name: str, usage: dict[str, SkillUsage], coverage: EvaluationCoverage
) -> bool:
    agent_loads = usage.get(name, SkillUsage()).loads_by_channel["agent"]
    eval_cases = coverage.routing_cases[name] + coverage.skill_cases[name]
    return bool(agent_loads) and not eval_cases


def usage_report(
    catalogue: dict[str, InstalledSkill],
    usage: dict[str, SkillUsage],
    coverage: EvaluationCoverage,
    days: int,
) -> str:
    unloaded = [name for name in sorted(catalogue) if name not in usage]
    uncovered = [
        name
        for name in ranked_skill_names(catalogue, usage)
        if is_agent_chosen_without_eval_case(name, usage, coverage)
    ]
    return "\n\n".join(
        [
            f"Skill loads in Claude Code transcripts over the last {days} days",
            aligned_table(report_rows(catalogue, usage, coverage)),
            f"Never loaded: {', '.join(unloaded) or 'none'}",
            f"Chosen by agents with no eval case: {', '.join(uncovered) or 'none'}",
        ]
    )


def prompts_report(loads, skill: str, limit: int) -> str:
    prompted_loads = sorted(
        (load for load in loads if load.skill == skill and load.prompt),
        key=lambda load: load.timestamp,
    )
    if not prompted_loads:
        return f"No prompt preceded an agent-chosen load of {skill}."
    return "\n".join(
        f"- {load.timestamp.date().isoformat()} {load.prompt}"
        for load in prompted_loads[-limit:]
    )


def parsed_arguments(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="skill-usage",
        description=(
            "Rank installed skills by how often Claude Code sessions loaded them, "
            "beside the eval cases that cover each one."
        ),
    )
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument(
        "--projects-directory", type=Path, default=Path.home() / ".claude" / "projects"
    )
    parser.add_argument("--plugin-root", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument(
        "--prompts",
        metavar="SKILL",
        help="print the latest real prompts that led an agent to load SKILL",
    )
    parser.add_argument("--limit", type=int, default=20)
    return parser.parse_args(arguments)


def main(arguments: list[str]) -> int:
    options = parsed_arguments(arguments)
    since = datetime.now(UTC) - timedelta(days=options.days)
    catalogue = installed_skills(options.plugin_root)
    if not catalogue:
        print(
            f"skill-usage: no installed skills under {options.plugin_root}",
            file=sys.stderr,
        )
        return 1
    if options.prompts:
        loads = skill_loads(options.projects_directory, since, with_prompts=True)
        print(prompts_report(loads, options.prompts, options.limit))
        return 0
    usage = usage_by_skill(skill_loads(options.projects_directory, since), catalogue)
    coverage = evaluation_coverage(options.repository)
    print(usage_report(catalogue, usage, coverage, options.days))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
