import os
import pathlib
import shutil
import subprocess
import xml.etree.ElementTree as ElementTree

import pytest

VERIFICATION_ROOT = pathlib.Path(__file__).resolve().parents[3]


def write_owned_tests(repository, framework):
    unit = repository / "home/base/fixture/__tests__/unit"
    integration = repository / "home/base/fixture/__tests__/integration"
    unit.mkdir(parents=True)
    integration.mkdir(parents=True)
    if framework == "pytest":
        (unit / "test_outcomes.py").write_text(
            "import os\nimport pytest\n"
            "def test_pass():\n    assert not os.environ.get('DOTFILES_TEST_REPORT_DIRECTORY')\n"
            "def test_fail():\n    assert False\n"
            "@pytest.mark.skip(reason='owned unexecuted case')\n"
            "def test_skip():\n    assert False\n"
        )
        (integration / "test_pass.py").write_text(
            "def test_integration_pass():\n    assert True\n"
        )
        return
    (unit / "outcomes.bats").write_text(
        '@test "pass" { test -z "$DOTFILES_TEST_REPORT_DIRECTORY"; }\n'
        '@test "fail" { false; }\n'
        '@test "skip" { skip "owned unexecuted case"; }\n'
    )
    (integration / "pass.bats").write_text('@test "integration pass" { true; }\n')


@pytest.mark.parametrize("framework", ["pytest", "bats"])
def test_native_reports_preserve_outcomes_and_separate_tiers(tmp_path, framework):
    if shutil.which(framework) is None:
        pytest.skip(f"{framework} is unavailable")
    repository = tmp_path / "owned repository"
    write_owned_tests(repository, framework)
    report_directory = tmp_path / "owned reports"
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$VERIFICATION_ROOT/runner/discovery.sh"\n'
            'source "$VERIFICATION_ROOT/runner/$FRAMEWORK.sh"\n'
            '"_run_${FRAMEWORK}_tier" unit quick\n'
            "unitStatus=$?\n"
            '"_run_${FRAMEWORK}_tier" integration integration-scripts\n'
            "integrationStatus=$?\n"
            'printf "statuses:%s,%s\\n" "$unitStatus" "$integrationStatus"\n',
        ],
        env={
            "PATH": os.environ["PATH"],
            "REPO_DIR": str(repository),
            "VERIFICATION_ROOT": str(VERIFICATION_ROOT),
            "FRAMEWORK": framework,
            "DOTFILES_TEST_REPORT_DIRECTORY": str(report_directory),
        },
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "statuses:1,0" in result.stdout, result.stdout + result.stderr
    paths = (
        [report_directory / f"pytest-{tier}.xml" for tier in ("unit", "integration")]
        if framework == "pytest"
        else [
            report_directory / f"bats-{tier}/report.xml"
            for tier in ("unit", "integration")
        ]
    )
    assert all(path.is_file() for path in paths), result.stdout + result.stderr
    unit_cases = ElementTree.parse(paths[0]).findall(".//testcase")
    integration_cases = ElementTree.parse(paths[1]).findall(".//testcase")
    assert len(unit_cases) == 3
    assert sum(case.find("failure") is not None for case in unit_cases) == 1
    assert sum(case.find("skipped") is not None for case in unit_cases) == 1
    assert len(integration_cases) == 1
    assert integration_cases[0].find("failure") is None
