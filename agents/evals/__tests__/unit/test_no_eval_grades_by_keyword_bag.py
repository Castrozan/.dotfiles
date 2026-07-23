from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
EVAL_CONFIG_DIR = REPO_ROOT / "agents" / "evals" / "config"


def eval_suite_files() -> list[Path]:
    return sorted(EVAL_CONFIG_DIR.glob("*.yaml")) + sorted(
        REPO_ROOT.glob("agents/skills/*/__tests__/evals/*.yaml")
    )


def suite_test_entries(suite_path: Path) -> list[dict]:
    document = yaml.safe_load(suite_path.read_text()) or {}
    return document.get("tests") or []


def every_authored_test() -> list[tuple[Path, dict]]:
    return [
        (suite_path, test)
        for suite_path in eval_suite_files()
        for test in suite_test_entries(suite_path)
    ]


def test_no_eval_grades_by_a_bag_of_alternative_keywords():
    offenders = [
        f"{suite_path.relative_to(REPO_ROOT)}:{test['name']}"
        for suite_path, test in every_authored_test()
        if "output_contains_any" in test.get("assertions", {})
    ]
    assert not offenders, (
        "these evals pass when any one of several loose keywords appears, which "
        f"grades vocabulary instead of substance: {offenders}"
    )


def test_every_positive_substring_assertion_is_an_exact_structured_token():
    loose = [
        (f"{suite_path.relative_to(REPO_ROOT)}:{test['name']}", expected)
        for suite_path, test in every_authored_test()
        for expected in test.get("assertions", {}).get("output_contains", [])
        if " " in str(expected)
    ]
    assert not loose, (
        "a positive substring assertion may only match an exact structured token "
        f"such as a sentinel, marker, or filename, not a phrase: {loose}"
    )


def test_the_keyword_bag_scan_covers_every_authored_eval():
    assert len(eval_suite_files()) > 15
    assert len(every_authored_test()) > 100
