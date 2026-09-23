import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "count,ceiling,exit_code,message",
    [
        (15, None, 0, "OK"),
        (16, None, 1, "limit 15"),
        (20, 20, 0, "OK"),
        (21, 20, 1, "limit 20"),
        (19, 20, 1, "lower its ceiling to 19"),
        (15, 20, 1, "remove its baseline entry"),
    ],
)
def test_ci_enforces_limits_and_ratchets_existing_ceilings(
    tmp_path, capsys, count, ceiling, exit_code, message
):
    path = Path(__file__).resolve().parents[2] / "check.py"
    specification = importlib.util.spec_from_file_location(
        "directory_entry_check", path
    )
    checker = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(checker)
    checker.REPOSITORY_ROOT = tmp_path
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    source = tmp_path / "source"
    source.mkdir()
    for index in range(count):
        (source / f"file{index}.py").touch()
    if ceiling:
        baseline = (
            tmp_path / "repository/verification/quality/directory-entries/baseline.json"
        )
        baseline.parent.mkdir(parents=True)
        baseline.write_text(json.dumps({"source": ceiling}))
    assert checker.main() == exit_code
    output = capsys.readouterr()
    assert message in output.out + output.err


@pytest.mark.parametrize("root_ceiling", [None, 30])
def test_ci_exempts_repository_root(tmp_path, root_ceiling):
    path = Path(__file__).resolve().parents[2] / "check.py"
    specification = importlib.util.spec_from_file_location(
        "directory_entry_check", path
    )
    checker = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(checker)
    checker.REPOSITORY_ROOT = tmp_path
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    for index in range(20):
        (tmp_path / f"file{index}.py").touch()
    if root_ceiling:
        baseline = (
            tmp_path / "repository/verification/quality/directory-entries/baseline.json"
        )
        baseline.parent.mkdir(parents=True)
        baseline.write_text(json.dumps({".": root_ceiling}))
    assert checker.main() == 0
