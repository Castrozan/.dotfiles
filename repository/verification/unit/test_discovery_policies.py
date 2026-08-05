import os
import pathlib
import platform
import shutil
import subprocess

HARNESS_TESTS_ROOT = pathlib.Path(__file__).resolve().parent.parent
DISCOVERY_LIBRARY = HARNESS_TESTS_ROOT / "runner" / "discovery.sh"
LINUX_ONLY_TEST_ROOTS_FILE = HARNESS_TESTS_ROOT / "runner" / "linux-only-test-roots.txt"

UNIT_TIER_TEST_PATTERN = "*/__tests__/unit/test_*.py"

LINUX_ONLY_CAPABILITY = LINUX_ONLY_TEST_ROOTS_FILE.read_text().split()[0]
SHARED_CAPABILITY_MODULE = "machine-configuration/included_capability"
AGENT_HARNESS_MODULE = "agent-harness/included_harness"
PRUNED_MODULES = (
    "private-configuration/pruned_submodule",
    ".worktrees/pruned_worktree",
)

PLANTED_TEST_MODULE_DIRECTORIES = (
    AGENT_HARNESS_MODULE,
    LINUX_ONLY_CAPABILITY,
    SHARED_CAPABILITY_MODULE,
    *PRUNED_MODULES,
)


def _plant_unit_test_under_each_module(fake_repository_root):
    for module_directory in PLANTED_TEST_MODULE_DIRECTORIES:
        unit_directory = fake_repository_root / module_directory / "__tests__" / "unit"
        unit_directory.mkdir(parents=True)
        (unit_directory / "test_planted.py").write_text(
            "def test_planted():\n    assert True\n"
        )


def _relative_planted_test(module_directory):
    return f"{module_directory}/__tests__/unit/test_planted.py"


def _discover_with_policy(fake_repository_root, discovery_policy):
    bash_executable = shutil.which("bash") or "/bin/bash"
    shell_program = (
        f"source {DISCOVERY_LIBRARY}\n"
        f'_discover_test_files "{discovery_policy}" "{UNIT_TIER_TEST_PATTERN}"\n'
    )
    completed = subprocess.run(
        [bash_executable, "-c", shell_program],
        env={"PATH": os.environ.get("PATH", ""), "REPO_DIR": str(fake_repository_root)},
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, (
        f"discovery returned {completed.returncode}\nstderr: {completed.stderr}"
    )
    discovered_relative_paths = set()
    for absolute_path_line in completed.stdout.splitlines():
        if absolute_path_line:
            discovered_relative_paths.add(
                str(pathlib.Path(absolute_path_line).relative_to(fake_repository_root))
            )
    return discovered_relative_paths


def test_platform_scoped_discovery_excludes_foreign_platform_and_pruned_dirs(tmp_path):
    fake_repository_root = tmp_path / "repo"
    _plant_unit_test_under_each_module(fake_repository_root)

    discovered = _discover_with_policy(fake_repository_root, "platform-scoped")

    assert _relative_planted_test(AGENT_HARNESS_MODULE) in discovered
    assert _relative_planted_test(SHARED_CAPABILITY_MODULE) in discovered
    if platform.system() == "Darwin":
        assert _relative_planted_test(LINUX_ONLY_CAPABILITY) not in discovered
    else:
        assert _relative_planted_test(LINUX_ONLY_CAPABILITY) in discovered
    for pruned_module in PRUNED_MODULES:
        assert _relative_planted_test(pruned_module) not in discovered


def test_cross_platform_discovery_includes_both_platforms_but_prunes_vendored(tmp_path):
    fake_repository_root = tmp_path / "repo"
    _plant_unit_test_under_each_module(fake_repository_root)

    discovered = _discover_with_policy(fake_repository_root, "cross-platform")

    assert _relative_planted_test(AGENT_HARNESS_MODULE) in discovered
    assert _relative_planted_test(LINUX_ONLY_CAPABILITY) in discovered
    assert _relative_planted_test(SHARED_CAPABILITY_MODULE) in discovered
    for pruned_module in PRUNED_MODULES:
        assert _relative_planted_test(pruned_module) not in discovered
