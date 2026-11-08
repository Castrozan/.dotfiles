import shlex
import subprocess

from evaluation_suite_support import load_suite_cases
from instructions.instruction_surface_scanner import REPO_ROOT

MINIMUM_ADVERSARIAL_CASES = 4
VERDICT_TIMEOUT_SECONDS = 60
BLOCKED_VERDICT = "BLOQUEADO"
ALLOWED_VERDICT = "LIBERADO"


def verdict_output(case):
    completed = subprocess.run(
        shlex.split(case["comando"]),
        input=case["entrada"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
        timeout=VERDICT_TIMEOUT_SECONDS,
    )
    return completed.stdout


def unmet_expectations(case, output):
    assertions = case["assercoes"]
    return [
        *[
            f"missing {text!r}"
            for text in assertions.get("contem", [])
            if text not in output
        ],
        *[
            f"unexpected {text!r}"
            for text in assertions.get("nao_contem", [])
            if text in output
        ],
    ]


def test_the_adversarial_axis_is_all_deterministic_hook_cases():
    cases = load_suite_cases("adversarial")
    assert len(cases) >= MINIMUM_ADVERSARIAL_CASES, (
        "the adversarial injection axis lost coverage; it must keep exercising the "
        "guards that stop an injected instruction from rewriting the agent's own "
        "rules or mass-staging unrelated work"
    )
    assert all(case["tipo"] == "cli" for case in cases)


def test_the_adversarial_axis_keeps_a_blocking_case_and_a_benign_control():
    verdicts = [
        case["assercoes"]["contem"][0] for case in load_suite_cases("adversarial")
    ]
    assert BLOCKED_VERDICT in verdicts, (
        "no blocking case: the axis would pass even with every guard off"
    )
    assert ALLOWED_VERDICT in verdicts, (
        "no benign control: the axis would pass even if a guard blocked everything"
    )


def test_every_adversarial_guard_still_behaves_as_asserted():
    failures = {}
    for case in load_suite_cases("adversarial"):
        unmet = unmet_expectations(case, verdict_output(case))
        if unmet:
            failures[case["nome"]] = unmet
    assert not failures, f"adversarial guards regressed: {failures}"
