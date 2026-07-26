import copy

from run_evals_significance import paired_comparison
from run_evals_test_runner import run_tests

INSTRUCTION_SURFACE_FIELDS = (
    "system_prompt",
    "skill_path",
    "agent",
    "extra_skill_paths",
)


def build_instruction_stripped_variant(config: dict) -> dict:
    control = copy.deepcopy(config)
    for tests in control.get("tests", {}).values():
        for test in tests:
            for field in INSTRUCTION_SURFACE_FIELDS:
                test.pop(field, None)
    return control


def outcomes_by_name(results: list) -> dict:
    return {result.name: result.passed for result in results}


def run_instruction_loading_experiment(
    config: dict,
    category: str | None = None,
    max_workers_override: int | None = None,
) -> dict:
    with_instructions = run_tests(
        config, category=category, max_workers_override=max_workers_override
    )
    without_instructions = run_tests(
        build_instruction_stripped_variant(config),
        category=category,
        max_workers_override=max_workers_override,
    )
    return paired_comparison(
        outcomes_by_name(with_instructions),
        outcomes_by_name(without_instructions),
    )
