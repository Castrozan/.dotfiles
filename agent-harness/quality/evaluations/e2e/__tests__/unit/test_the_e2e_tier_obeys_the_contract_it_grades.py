from pathlib import Path

from e2e_assertions_naming import check_workspace_file_descriptive_names_assertion
from e2e_assertions_comments import check_workspace_file_no_comments_assertion

E2E_PACKAGE_DIRECTORY = Path(__file__).resolve().parent.parent.parent


def graded_python_sources() -> list[str]:
    return sorted(
        str(path.relative_to(E2E_PACKAGE_DIRECTORY))
        for path in E2E_PACKAGE_DIRECTORY.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def sources_failing(assertion_check) -> dict[str, str]:
    return {
        relative_path: result.detail
        for relative_path in graded_python_sources()
        for result in [assertion_check(E2E_PACKAGE_DIRECTORY, relative_path)]
        if not result.passed
    }


def test_the_tier_finds_its_own_sources():
    assert "e2e_assertions_naming.py" in graded_python_sources()


def test_every_e2e_source_passes_the_descriptive_name_contract_it_grades():
    failures = sources_failing(check_workspace_file_descriptive_names_assertion)
    assert not failures, failures


def test_every_e2e_source_passes_the_no_comments_contract_it_grades():
    failures = sources_failing(check_workspace_file_no_comments_assertion)
    assert not failures, failures
