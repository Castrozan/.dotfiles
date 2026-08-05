import pathlib
import re
import subprocess

REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[5]
TESTS_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "tests.yml"
VERIFICATION_ROOT = REPOSITORY_ROOT / "repository" / "verification"
TEST_RUNNER = VERIFICATION_ROOT / "run.sh"
DISCOVERY_LIBRARY = VERIFICATION_ROOT / "runner" / "discovery.sh"

CI_TIER_CHECKS_PATTERN = re.compile(r"CI_TIER_CHECKS=\((.*?)\n\)", re.DOTALL)

BATS_TIER_FUNCTION_NAMES = {
    "unit": ("_run_quick_bats_tests", "_run_quick_bats_tests_ci"),
    "integration": ("_run_integration_scripts_bats_tests",),
}

LUA_TIER_FUNCTION_NAME = "_run_lua_unit_tests"
LUA_TEST_PATTERN = "*/__tests__/*_test.lua"


def checks_the_continuous_integration_tier_runs():
    match = CI_TIER_CHECKS_PATTERN.search(TEST_RUNNER.read_text())
    assert match, (
        "run.sh no longer declares CI_TIER_CHECKS, so this gate cannot tell what "
        "continuous integration actually runs and would pass without inspecting "
        "anything"
    )
    return set(match.group(1).split())


def discovered_test_files(discovery_policy, path_pattern):
    completed = subprocess.run(
        [
            "bash",
            "-c",
            f'export REPO_DIR="{REPOSITORY_ROOT}"; source "{DISCOVERY_LIBRARY}"; '
            f'_discover_test_files {discovery_policy} "{path_pattern}"',
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, (
        "discovery failed to run, so every tier below would look empty and this gate "
        "would pass without inspecting anything. A moved discovery library is the "
        f"usual cause. Exit {completed.returncode}, stderr: {completed.stderr}"
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def test_every_bats_tier_holding_tests_runs_in_continuous_integration():
    invoked_checks = checks_the_continuous_integration_tier_runs()
    uncovered_tiers = {}
    for tier_directory_name, tier_functions in BATS_TIER_FUNCTION_NAMES.items():
        if invoked_checks.intersection(tier_functions):
            continue
        discovered = discovered_test_files(
            "platform-scoped", f"*/__tests__/{tier_directory_name}/*.bats"
        )
        if discovered:
            uncovered_tiers[tier_directory_name] = len(discovered)

    assert not uncovered_tiers, (
        "these bats tiers hold tests that no continuous integration job runs, so they "
        "gate nothing on a push and rot until someone runs them by hand. Tier -> file "
        f"count: {uncovered_tiers}. The CI tier invokes: {sorted(invoked_checks)}"
    )


def test_the_lua_tier_runs_in_continuous_integration_when_it_holds_tests():
    if LUA_TIER_FUNCTION_NAME in TESTS_WORKFLOW.read_text():
        return
    if LUA_TIER_FUNCTION_NAME in checks_the_continuous_integration_tier_runs():
        return

    discovered = discovered_test_files("cross-platform", LUA_TEST_PATTERN)
    assert not discovered, (
        f"{len(discovered)} lua test files exist but no workflow calls "
        f"{LUA_TIER_FUNCTION_NAME}, so they gate nothing on a push. They are "
        "pure-logic suites that run identically on either platform, so there is no "
        "environment reason to leave them out"
    )
