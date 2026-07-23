import os
import pathlib
import platform
import shutil
import subprocess

HARNESS_TESTS_ROOT = pathlib.Path(__file__).resolve().parent.parent
DISCOVERY_LIBRARY = HARNESS_TESTS_ROOT / "lib" / "discovery.sh"

UNIT_TIER_TEST_PATTERN = "*/__tests__/unit/test_*.py"

PLANTED_TEST_MODULE_DIRECTORIES = (
    "home/base/included_module",
    "home/linux/linux_only_module",
    "home/darwin/darwin_only_module",
    "private-config/pruned_submodule",
    ".worktrees/pruned_worktree",
)

CURRENT_PLATFORM_MODULE = (
    "home/darwin/darwin_only_module"
    if platform.system() == "Darwin"
    else "home/linux/linux_only_module"
)
FOREIGN_PLATFORM_MODULE = (
    "home/linux/linux_only_module"
    if platform.system() == "Darwin"
    else "home/darwin/darwin_only_module"
)
PRUNED_MODULES = (
    "private-config/pruned_submodule",
    ".worktrees/pruned_worktree",
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

    assert _relative_planted_test("home/base/included_module") in discovered
    assert _relative_planted_test(CURRENT_PLATFORM_MODULE) in discovered
    assert _relative_planted_test(FOREIGN_PLATFORM_MODULE) not in discovered
    for pruned_module in PRUNED_MODULES:
        assert _relative_planted_test(pruned_module) not in discovered


def test_cross_platform_discovery_includes_both_platforms_but_prunes_vendored(tmp_path):
    fake_repository_root = tmp_path / "repo"
    _plant_unit_test_under_each_module(fake_repository_root)

    discovered = _discover_with_policy(fake_repository_root, "cross-platform")

    assert _relative_planted_test("home/base/included_module") in discovered
    assert _relative_planted_test("home/linux/linux_only_module") in discovered
    assert _relative_planted_test("home/darwin/darwin_only_module") in discovered
    for pruned_module in PRUNED_MODULES:
        assert _relative_planted_test(pruned_module) not in discovered
