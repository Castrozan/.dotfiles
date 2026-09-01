import time
from dataclasses import dataclass

from run_evals_assertions import check_assertions
from run_evals_hook_test_runner import evaluate_hook_test
from run_evals_judge import JudgeInvocationError, build_llm_judge
from run_evals_config_loader import resolve_system_prompt_for_test
import run_evals_subject_port as subject_port


@dataclass
class TestResult:
    __test__ = False

    name: str
    passed: bool
    duration: float
    output: str
    assertions_failed: list[str]
    error: str | None = None
    category: str = "other"


def run_test(
    test: dict,
    settings: dict,
    dry_run: bool = False,
    authored_category: str = "other",
    instruction_ref: str | None = None,
    harness: str = "claude",
    judge_harness: str = "claude",
) -> TestResult:
    name = test["name"]
    model = subject_port.model_for_harness(
        test, harness, settings.get("subject_models", {"claude": "sonnet"})
    )
    model_reasoning_effort = settings.get("subject_reasoning_efforts", {}).get(harness)
    timeout = settings.get("timeout_seconds", 120)

    if test.get("type") == "hook_test":
        hook_start_time = time.time()
        hook_failures = evaluate_hook_test(test)
        return TestResult(
            name=name,
            passed=len(hook_failures) == 0,
            duration=time.time() - hook_start_time,
            output="[hook_test]",
            assertions_failed=hook_failures,
            category=authored_category,
        )

    prompt = test.get("prompt")
    if not prompt:
        return TestResult(
            name=name,
            passed=False,
            duration=0,
            output="",
            assertions_failed=[],
            error="Test missing 'prompt' field",
            category=authored_category,
        )

    if dry_run:
        return TestResult(
            name=name,
            passed=True,
            duration=0,
            output="[DRY RUN]",
            assertions_failed=[],
            category=authored_category,
        )

    start_time = time.time()

    resolved_system_prompt = resolve_system_prompt_for_test(test, instruction_ref)
    if instruction_ref and test.get("skill_path") and resolved_system_prompt is None:
        return TestResult(
            name=name,
            passed=False,
            duration=0,
            output="",
            assertions_failed=[],
            error=f"instruction surface not found at Git ref {instruction_ref}",
            category=authored_category,
        )

    output, success = subject_port.invoke_subject(
        harness,
        prompt=prompt,
        model=model,
        model_reasoning_effort=model_reasoning_effort,
        system_prompt=resolved_system_prompt,
        timeout=timeout,
        no_tools=test.get("no_tools", False),
        invocation_role="subject",
    )

    duration = time.time() - start_time

    if not success:
        return TestResult(
            name=name,
            passed=False,
            duration=duration,
            output=output[:500],
            assertions_failed=[],
            error=output,
            category=authored_category,
        )

    assertions = test.get("assertions", {})
    judge = None
    if "llm_judge" in assertions:
        judge = build_llm_judge(
            settings.get("judge_models", {"claude": "opus"})[judge_harness],
            subject_port.build_provider_invoker(
                judge_harness,
                timeout,
                settings.get("judge_reasoning_efforts", {}).get(judge_harness),
            ),
        )
    try:
        failures = check_assertions(output, assertions, judge=judge)
    except JudgeInvocationError as error:
        return TestResult(
            name=name,
            passed=False,
            duration=duration,
            output=output[:500],
            assertions_failed=[],
            error=str(error),
            category=authored_category,
        )

    return TestResult(
        name=name,
        passed=len(failures) == 0,
        duration=duration,
        output=output[:500],
        assertions_failed=failures,
        category=authored_category,
    )
