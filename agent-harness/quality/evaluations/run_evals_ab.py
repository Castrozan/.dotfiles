import copy

from run_evals_significance import paired_comparison, paired_hierarchical_bootstrap
from run_evals_evidence import raise_for_evaluation_errors
from run_evals_suite_runner import run_tests

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


def outcome_key(result) -> str:
    return f"{result.category}::{result.name}"


def outcomes_by_name(results: list) -> dict:
    return {outcome_key(result): result.passed for result in results}


def append_outcomes(target: dict[str, list[bool]], results: list) -> None:
    for result in results:
        target.setdefault(outcome_key(result), []).append(result.passed)


def run_instruction_loading_experiment(
    config: dict,
    category: str | None = None,
    max_workers_override: int | None = None,
    epochs: int = 1,
    comparison_ref: str | None = None,
    dry_run: bool = False,
    harness: str = "claude",
    judge_harness: str = "claude",
) -> dict:
    variant_a: dict[str, list[bool]] = {}
    variant_b: dict[str, list[bool]] = {}
    control_config = (
        config if comparison_ref else build_instruction_stripped_variant(config)
    )

    def run_candidate():
        return run_tests(
            config,
            category=category,
            max_workers_override=max_workers_override,
            dry_run=dry_run,
            harness=harness,
            judge_harness=judge_harness,
        )

    def run_control():
        return run_tests(
            control_config,
            category=category,
            max_workers_override=max_workers_override,
            instruction_ref=comparison_ref,
            dry_run=dry_run,
            harness=harness,
            judge_harness=judge_harness,
        )

    for epoch_index in range(epochs):
        if epoch_index % 2 == 0:
            candidate_results = run_candidate()
            control_results = run_control()
        else:
            control_results = run_control()
            candidate_results = run_candidate()
        raise_for_evaluation_errors(candidate_results, "candidate arm")
        raise_for_evaluation_errors(control_results, "control arm")
        append_outcomes(variant_a, candidate_results)
        append_outcomes(variant_b, control_results)

    if epochs == 1:
        return paired_comparison(
            {name: outcomes[0] for name, outcomes in variant_a.items()},
            {name: outcomes[0] for name, outcomes in variant_b.items()},
        )
    return paired_hierarchical_bootstrap(variant_a, variant_b)
