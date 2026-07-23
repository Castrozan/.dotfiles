#!/usr/bin/env python3
import pathlib
import re

REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parent.parent
TESTS_DIRECTORY_NAME = "__tests__"
TIER_DIRECTORY_NAMES = ["unit", "integration", "e2e"]
EXCLUDED_PATH_SEGMENTS = {
    ".git",
    "node_modules",
    "private-config",
    ".deep-work",
    ".direnv",
    ".worktrees",
    "__pycache__",
    "result",
}

BATS_TEST_BLOCK_PATTERN = re.compile(r"^\s*@test\b")
PYTEST_TEST_FUNCTION_PATTERN = re.compile(r"^\s*def test_")
NIX_EVAL_CHECK_PATTERN = re.compile(r"\bmkEvalCheck\b")


def path_is_excluded(path):
    return any(segment in EXCLUDED_PATH_SEGMENTS for segment in path.parts)


def discover_tests_directories():
    return sorted(
        directory
        for directory in REPOSITORY_ROOT.rglob(TESTS_DIRECTORY_NAME)
        if directory.is_dir()
        and not path_is_excluded(directory.relative_to(REPOSITORY_ROOT))
    )


def count_matching_lines(file_path, pattern):
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0
    return sum(1 for line in text.splitlines() if pattern.search(line))


def count_pattern_occurrences(file_path, pattern):
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0
    return len(pattern.findall(text))


def summarize_tier(tests_directory, tier_directory_name):
    tier_directory = tests_directory / tier_directory_name
    if not tier_directory.is_dir():
        return None
    bats_blocks = sum(
        count_matching_lines(bats_file, BATS_TEST_BLOCK_PATTERN)
        for bats_file in tier_directory.glob("*.bats")
    )
    pytest_functions = sum(
        count_matching_lines(python_file, PYTEST_TEST_FUNCTION_PATTERN)
        for python_file in tier_directory.glob("test_*.py")
    )
    if bats_blocks == 0 and pytest_functions == 0:
        return None
    return {"bats_blocks": bats_blocks, "pytest_functions": pytest_functions}


def summarize_tests_directory(tests_directory):
    tiers = {}
    for tier_directory_name in TIER_DIRECTORY_NAMES:
        tier_summary = summarize_tier(tests_directory, tier_directory_name)
        if tier_summary is not None:
            tiers[tier_directory_name] = tier_summary

    lua_test_files = list(tests_directory.glob("*_test.lua"))
    qml_runner = tests_directory / "qml" / "run-qml-tests.sh"
    eval_yaml_files = list((tests_directory / "evals").glob("*.yaml"))
    checks_nix_file = tests_directory / "checks.nix"

    return {
        "tiers": tiers,
        "lua_test_file_count": len(lua_test_files),
        "has_qml_runner": qml_runner.is_file(),
        "eval_yaml_count": len(eval_yaml_files),
        "eval_check_count": (
            count_pattern_occurrences(checks_nix_file, NIX_EVAL_CHECK_PATTERN)
            if checks_nix_file.is_file()
            else 0
        ),
        "has_checks_nix": checks_nix_file.is_file(),
    }


def owning_module_label(tests_directory):
    relative_parent = tests_directory.parent.relative_to(REPOSITORY_ROOT)
    return "." if str(relative_parent) == "." else str(relative_parent)


def format_summary_lines(summary):
    lines = []
    for tier_directory_name in TIER_DIRECTORY_NAMES:
        tier_summary = summary["tiers"].get(tier_directory_name)
        if tier_summary is None:
            continue
        parts = []
        if tier_summary["bats_blocks"]:
            parts.append(f"{tier_summary['bats_blocks']} bats @test")
        if tier_summary["pytest_functions"]:
            parts.append(f"{tier_summary['pytest_functions']} pytest fn")
        lines.append(f"    {tier_directory_name}: {', '.join(parts)}")
    if summary["lua_test_file_count"]:
        lines.append(f"    lua: {summary['lua_test_file_count']} suite")
    if summary["has_qml_runner"]:
        lines.append("    qml: 1 suite")
    if summary["eval_yaml_count"]:
        lines.append(f"    evals: {summary['eval_yaml_count']} yaml")
    if summary["has_checks_nix"]:
        lines.append(f"    checks.nix: {summary['eval_check_count']} eval-check")
    return lines


def main():
    tests_directories = discover_tests_directories()
    totals = {
        "modules": 0,
        "bats_blocks": 0,
        "pytest_functions": 0,
        "lua_suites": 0,
        "qml_suites": 0,
        "eval_yamls": 0,
        "eval_checks": 0,
    }

    print(f"=== Test Suite Map ({len(tests_directories)} __tests__ directories) ===\n")
    for tests_directory in tests_directories:
        summary = summarize_tests_directory(tests_directory)
        summary_lines = format_summary_lines(summary)
        if not summary_lines:
            continue
        totals["modules"] += 1
        for tier_summary in summary["tiers"].values():
            totals["bats_blocks"] += tier_summary["bats_blocks"]
            totals["pytest_functions"] += tier_summary["pytest_functions"]
        totals["lua_suites"] += summary["lua_test_file_count"]
        totals["qml_suites"] += 1 if summary["has_qml_runner"] else 0
        totals["eval_yamls"] += summary["eval_yaml_count"]
        totals["eval_checks"] += summary["eval_check_count"]

        print(owning_module_label(tests_directory))
        for line in summary_lines:
            print(line)

    print(
        "\n=== Totals ===\n"
        f"  modules with tests: {totals['modules']}\n"
        f"  bats @test blocks:  {totals['bats_blocks']}\n"
        f"  pytest functions:   {totals['pytest_functions']}\n"
        f"  lua suites:         {totals['lua_suites']}\n"
        f"  qml suites:         {totals['qml_suites']}\n"
        f"  eval yamls:         {totals['eval_yamls']}\n"
        f"  nix eval-checks:    {totals['eval_checks']}"
    )


if __name__ == "__main__":
    main()
