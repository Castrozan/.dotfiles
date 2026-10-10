from collections import Counter

from instructions.instruction_surface_scanner import public_skill_definition_path
from runner.execution.run_evals_hook_test_runner import HOOK_ASSERTION_NAMES
from runner.judging.run_evals_assertions import OUTPUT_ASSERTION_NAMES
from runner.run_evals_worktree_and_environment import REPO_ROOT


def evaluation_configuration_failures(config: dict) -> list[str]:
    return [
        failure
        for category, tests in config.get("tests", {}).items()
        for failure in _category_contract_failures(category, tests)
    ]


def _category_contract_failures(category: str, tests: list[dict]) -> list[str]:
    return _duplicate_configuration_failures(category, tests) + [
        f"{category}::{test.get('name')}: {failure}"
        for test in tests
        for failure in _test_contract_failures(test)
    ]


def _duplicate_configuration_failures(category: str, tests: list[dict]) -> list[str]:
    names = Counter(test.get("name") for test in tests)
    return [
        f"{category}: duplicate evaluation name {name}"
        for name, count in names.items()
        if count > 1
    ]


def _test_contract_failures(test: dict) -> list[str]:
    failures = []
    if not test.get("name"):
        failures.append("missing name")
    return (
        failures
        + _assertion_contract_failures(test)
        + _prompt_contract_failures(test)
        + _instruction_contract_failures(test)
    )


def _assertion_contract_failures(test: dict) -> list[str]:
    assertions = test.get("assertions")
    if not isinstance(assertions, dict):
        return ["invalid assertions"]
    if not assertions:
        return ["missing assertions"]
    supported = (
        HOOK_ASSERTION_NAMES
        if test.get("type") == "hook_test"
        else OUTPUT_ASSERTION_NAMES
    )
    unsupported = [
        f"unsupported assertion {name}" for name in sorted(set(assertions) - supported)
    ]
    return unsupported + _assertion_content_failures(test, assertions)


def _assertion_content_failures(test: dict, assertions: dict) -> list[str]:
    if test.get("type") == "hook_test":
        return _hook_assertion_content_failures(assertions)
    return [
        f"invalid criteria for assertion {name}"
        for name, criteria in assertions.items()
        if not _assertion_list_is_valid(name, criteria)
    ]


def _assertion_list_is_valid(name: str, criteria) -> bool:
    if not isinstance(criteria, list):
        return False
    if not criteria:
        return False
    return all(_assertion_criterion_is_valid(name, criterion) for criterion in criteria)


def _assertion_criterion_is_valid(name: str, criterion) -> bool:
    if name == "llm_judge" and isinstance(criterion, dict):
        criterion = criterion.get("rubric")
    if not isinstance(criterion, str):
        return False
    if name == "output_equals":
        return True
    return bool(criterion.strip())


def _hook_assertion_content_failures(assertions: dict) -> list[str]:
    field_types = {
        "hook_blocks": bool,
        "message_contains": str,
        "message_does_not_contain": str,
    }
    return [
        f"invalid value for hook assertion {name}"
        for name in set(assertions) & set(field_types)
        if not _hook_assertion_value_is_valid(assertions[name], field_types[name])
    ]


def _hook_assertion_value_is_valid(value, expected_type) -> bool:
    return isinstance(value, expected_type) and value != ""


def _prompt_contract_failures(test: dict) -> list[str]:
    if test.get("type") == "hook_test":
        return []
    prompt = test.get("prompt")
    if not isinstance(prompt, str):
        return ["missing prompt"]
    if not prompt.strip():
        return ["missing prompt"]
    return []


def _primary_instruction_path(test: dict):
    if test.get("skill_path"):
        return test["skill_path"]
    if test.get("agent"):
        return public_skill_definition_path(test["agent"], REPO_ROOT)
    return None


def _instruction_contract_failures(test: dict) -> list[str]:
    if "system_prompt" in test:
        return []
    primary_path = _primary_instruction_path(test)
    return _agent_contract_failures(test, primary_path) + [
        f"missing instruction source {path}"
        for path in _instruction_source_paths(test, primary_path)
        if not (REPO_ROOT / path).is_file()
    ]


def _instruction_source_paths(test: dict, primary_path) -> list:
    paths = [primary_path] if primary_path else []
    paths.extend(test.get("extra_skill_paths") or [])
    return paths


def _agent_contract_failures(test: dict, primary_path) -> list[str]:
    if test.get("agent") and not test.get("skill_path") and primary_path is None:
        return [f"unknown instruction agent {test['agent']}"]
    return []
