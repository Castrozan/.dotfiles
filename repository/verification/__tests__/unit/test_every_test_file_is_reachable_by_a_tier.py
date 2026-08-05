import pathlib
import subprocess

VERIFICATION_ROOT = pathlib.Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = VERIFICATION_ROOT.parents[1]
RUNNER_DIRECTORY = VERIFICATION_ROOT / "runner"
DISCOVERY_LIBRARY = RUNNER_DIRECTORY / "discovery.sh"

TIER_DIRECTORY_NAMES = ("unit", "integration", "e2e")

TIER_COLLECTOR_LIBRARIES = ("bats.sh", "pytest.sh", "lua.sh")

PRUNED_DIRECTORY_NAMES = {
    ".git",
    "node_modules",
    "private-configuration",
    "result",
    ".deep-work",
    ".direnv",
    ".worktrees",
    "__pycache__",
    ".pytest_cache",
}


def files_a_tier_collector_returns(collector_invocation):
    sourced_libraries = "; ".join(
        f'source "{RUNNER_DIRECTORY}/{library}"' for library in TIER_COLLECTOR_LIBRARIES
    )
    completed = subprocess.run(
        [
            "bash",
            "-c",
            f'export REPO_DIR="{REPOSITORY_ROOT}"; source "{DISCOVERY_LIBRARY}"; '
            f"{sourced_libraries}; {collector_invocation}",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, (
        f"the tier collector failed to run, so every tier would look empty and this "
        f"gate would pass without inspecting anything. Invocation: "
        f"{collector_invocation}, exit {completed.returncode}, stderr: "
        f"{completed.stderr}"
    )
    return {
        pathlib.Path(line) for line in completed.stdout.splitlines() if line.strip()
    }


def every_file_a_tier_reaches():
    reached = files_a_tier_collector_returns("_collect_lua_test_files")
    for tier_directory_name in TIER_DIRECTORY_NAMES:
        reached |= files_a_tier_collector_returns(
            f"_collect_bats_test_files_in_tier_directory {tier_directory_name}"
        )
        reached |= files_a_tier_collector_returns(
            f"_collect_pytest_test_files_in_tier_directory {tier_directory_name}"
        )
    return reached


def foreign_platform_test_roots():
    completed = subprocess.run(
        [
            "bash",
            "-c",
            f'source "{RUNNER_DIRECTORY}/foreign-platform-test-roots.sh"; '
            "_foreign_platform_test_roots",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return [
        REPOSITORY_ROOT / line.strip()
        for line in completed.stdout.splitlines()
        if line.strip()
    ]


def every_file_that_looks_like_a_test():
    foreign_roots = foreign_platform_test_roots()
    candidates = set()
    for path in REPOSITORY_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if PRUNED_DIRECTORY_NAMES.intersection(path.parts):
            continue
        if any(part.startswith("result-") for part in path.parts):
            continue
        if any(root in path.parents for root in foreign_roots):
            continue
        if (
            path.suffix == ".bats"
            or (path.suffix == ".py" and path.name.startswith("test_"))
            or path.name.endswith("_test.lua")
        ):
            candidates.add(path)
    return candidates


def test_the_repository_holds_a_real_corpus_of_test_files():
    assert len(every_file_that_looks_like_a_test()) > 100, (
        "almost no test files were found, so the gate below would pass without "
        "inspecting anything"
    )


def test_no_test_file_sits_where_the_tiers_cannot_reach_it():
    unreachable = sorted(
        str(path.relative_to(REPOSITORY_ROOT))
        for path in every_file_that_looks_like_a_test() - every_file_a_tier_reaches()
    )
    assert not unreachable, (
        "no tier collector reaches these test files, so they run nowhere and rot: no "
        "push turns red when they break. A test file belongs under a "
        f"__tests__/{{{','.join(TIER_DIRECTORY_NAMES)}}} directory, at any depth below "
        f"it. Unreachable files: {unreachable}"
    )
