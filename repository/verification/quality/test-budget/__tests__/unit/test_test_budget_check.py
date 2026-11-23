import importlib.util
import subprocess
from pathlib import Path

import pytest

GIT_TIMEOUT_SECONDS = 10
CHECK_PATH = Path(__file__).resolve().parents[2] / "check.py"


def budget_check():
    specification = importlib.util.spec_from_file_location(
        "test_budget_check", CHECK_PATH
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "count,expected_fragment",
    [(11, "never raise the budget"), (9, "lower its budget to 9"), (10, None)],
)
def test_a_suite_must_sit_exactly_on_its_budget(count, expected_fragment):
    failures = budget_check().budget_failures({"pytest": count}, {"pytest": 10})

    assert len(failures) == (expected_fragment is not None)
    assert all(expected_fragment in failure for failure in failures)


def test_a_suite_counts_only_its_own_tracked_test_functions(tmp_path):
    subprocess.run(
        ["git", "init", "--quiet", str(tmp_path)],
        check=True,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    (tmp_path / "test_sample.py").write_text(
        "def test_one():\n    pass\n\n\nasync def test_two():\n    pass\n\n\ndef helper():\n    pass\n"
    )
    (tmp_path / "sample.bats").write_text('@test "one" {\n\ttrue\n}\n')
    (tmp_path / "untracked.bats").write_text('@test "ignored" {\n\ttrue\n}\n')
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "test_sample.py", "sample.bats"],
        check=True,
        timeout=GIT_TIMEOUT_SECONDS,
    )

    assert budget_check().test_counts(tmp_path) == {"pytest": 2, "bats": 1, "qml": 0}
