import subprocess

import pytest

from directory_entry_guard_handler import handle
from directory_entry_policy import directory_entry_violations


@pytest.mark.parametrize("target_path", ["root20.py", "nested/allowed.py"])
def test_repository_root_has_no_entry_limit(tmp_path, target_path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    for index in range(20):
        (tmp_path / f"root{index}.py").touch()
    target = tmp_path / target_path
    assert (
        handle({"tool_name": "Write", "tool_input": {"file_path": str(target)}}) is None
    )


def test_only_nested_directories_produce_violations():
    violations = directory_entry_violations({".": 50, "source": 16}, {})
    assert [violation.directory for violation in violations] == ["source"]
