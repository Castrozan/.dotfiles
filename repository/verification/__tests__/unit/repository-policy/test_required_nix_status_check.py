import itertools
from pathlib import Path
import re
import subprocess

import pytest
import yaml


REPOSITORY = Path(__file__).resolve().parents[5]
WORKFLOW = REPOSITORY / ".github/workflows/nix-lint.yml"
RESULTS = ("success", "failure", "cancelled", "skipped")


def required_check():
    jobs = yaml.safe_load(WORKFLOW.read_text())["jobs"]
    candidates = [
        (identifier, job)
        for identifier, job in jobs.items()
        if job.get("name") == "Nix Lint"
    ]
    assert len(candidates) == 1
    identifier, gate = candidates[0]
    assert set(gate["needs"]) == set(jobs) - {identifier}
    assert gate["if"] == "${{ always() }}"
    return gate


def flake_checks_command():
    jobs = yaml.safe_load(WORKFLOW.read_text())["jobs"]
    entries = [
        entry
        for entry in jobs["evaluate"]["strategy"]["matrix"]["include"]
        if entry["name"] == "Nix flake checks"
    ]
    assert len(entries) == 1
    return entries[0]["command"]


def test_required_nix_check_covers_all_parallel_jobs():
    required_check()


def test_flake_checks_job_ends_on_the_complete_flake_check_verdict():
    command_lines = flake_checks_command().strip().splitlines()
    verdict = command_lines[-1]
    assert verdict.startswith("nix flake check --keep-going")
    assert "--no-build" not in verdict


def test_flake_checks_verdict_never_answers_from_the_evaluation_cache():
    assert "--no-eval-cache" in flake_checks_command().strip().splitlines()[-1]


@pytest.mark.parametrize(
    "lint_result,evaluation_result", list(itertools.product(RESULTS, repeat=2))
)
def test_required_nix_check_propagates_dependency_results(
    lint_result, evaluation_result
):
    gate = required_check()
    step = gate["steps"][0]
    outcomes = {"lint": lint_result, "evaluate": evaluation_result}
    environment = {}
    for name, expression in step["env"].items():
        match = re.fullmatch(r"\$\{\{ needs\.(\w+)\.result \}\}", expression)
        assert match is not None
        environment[name] = outcomes[match.group(1)]
    result = subprocess.run(
        ["bash", "-e", "-c", step["run"]],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert (result.returncode == 0) == all(
        outcome == "success" for outcome in outcomes.values()
    )
