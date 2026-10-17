import subprocess

import pytest
from e2e.assertions.e2e_assertions_workspace import (
    check_workspace_file_changed_assertion,
)
from e2e.sessions.e2e_workspace import setup_e2e_scenario_workspace


@pytest.mark.parametrize(
    "change_state", ["staged", "unstaged", "committed", "unchanged"]
)
def test_file_changes_include_the_index(tmp_path, change_state):
    setup_e2e_scenario_workspace(
        {
            "setup": {
                "git_init": True,
                "files": [{"path": "app.py", "content": "value = 1\n"}],
            }
        },
        tmp_path,
    )
    if change_state != "unchanged":
        (tmp_path / "app.py").write_text("value = 2\n")
    if change_state in {"staged", "committed"}:
        subprocess.run(["git", "add", "app.py"], cwd=tmp_path, check=True)
    if change_state == "committed":
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=test",
                "-c",
                "user.email=test@test",
                "commit",
                "-m",
                "change",
            ],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

    result = check_workspace_file_changed_assertion(tmp_path, "app.py")

    assert result.passed is (change_state != "unchanged")
