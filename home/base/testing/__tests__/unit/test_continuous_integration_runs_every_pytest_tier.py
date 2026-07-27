import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
TESTS_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "tests.yml"
DISCOVERY_LIBRARY = REPOSITORY_ROOT / "__tests__" / "lib" / "discovery.sh"

PYTEST_TIERS_THAT_MUST_RUN_IN_CONTINUOUS_INTEGRATION = ("unit", "integration")


def tiers_invoked_by_the_tests_workflow():
    workflow_text = TESTS_WORKFLOW.read_text()
    return {
        line.split()[1]
        for line in workflow_text.splitlines()
        if "_run_pytest_tier" in line and len(line.split()) >= 2
    }


def discovered_test_files_in_tier(tier_directory_name):
    completed = subprocess.run(
        [
            "bash",
            "-c",
            f'export REPO_DIR="{REPOSITORY_ROOT}"; source "{DISCOVERY_LIBRARY}"; '
            f'_discover_test_files platform-scoped "*/__tests__/{tier_directory_name}/test_*.py"',
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def test_every_pytest_tier_holding_tests_is_invoked_by_continuous_integration():
    invoked_tiers = tiers_invoked_by_the_tests_workflow()
    uncovered_tiers = {
        tier: len(discovered_test_files_in_tier(tier))
        for tier in PYTEST_TIERS_THAT_MUST_RUN_IN_CONTINUOUS_INTEGRATION
        if tier not in invoked_tiers and discovered_test_files_in_tier(tier)
    }
    assert not uncovered_tiers, (
        "run.sh discovers these tiers locally but no workflow invokes them, so the "
        "tests in them gate nothing on a push and can rot unnoticed. Tier -> file "
        f"count: {uncovered_tiers}. Workflow invokes: {sorted(invoked_tiers)}"
    )


def test_continuous_integration_supplies_the_binaries_the_suite_shells_out_to():
    workflow_text = TESTS_WORKFLOW.read_text()
    assert "test-suite-environment.nix" in workflow_text, (
        "the pytest jobs run inside a nix shell built from an expression, so every "
        "binary the tests shell out to has to come from that expression rather than "
        "from the runner image; memory-recall shells out to ripgrep and its tests "
        "fail with an unparseable empty hook response when it is absent"
    )
