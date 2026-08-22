import subprocess
import sys

import pytest
from agent_commit_provenance_hook_test_support import (
    HOOK_ENTRYPOINT_PATH,
    agent_session_environment,
    commit_a_change,
    install_repository_local_hook,
    latest_commit_message,
    repository_with_the_hook_installed,
    run_git,
)


@pytest.fixture
def repository(tmp_path):
    return repository_with_the_hook_installed(tmp_path)


def test_a_repository_local_hook_still_runs(repository):
    install_repository_local_hook(
        repository, '#!/bin/sh\nprintf "local hook was here\\n" >> "$1"\n'
    )
    commit_a_change(repository, "a.txt", "feat: chained")
    assert "local hook was here" in latest_commit_message(repository)


def test_a_repository_local_hook_can_still_veto_the_commit(repository):
    install_repository_local_hook(repository, "#!/bin/sh\nexit 3\n")
    assert commit_a_change(repository, "a.txt", "feat: vetoed").returncode != 0


def test_a_merge_commit_is_left_alone(repository):
    commit_a_change(repository, "a.txt", "feat: first")
    run_git(repository, "checkout", "-b", "side")
    commit_a_change(repository, "b.txt", "feat: side")
    run_git(repository, "checkout", "main")
    commit_a_change(repository, "c.txt", "feat: main")
    run_git(repository, "merge", "--no-ff", "side", "-m", "Merge branch side")
    assert latest_commit_message(repository) == "Merge branch side"


def test_an_empty_message_stays_empty_so_git_still_aborts(repository, tmp_path):
    message_file_path = tmp_path / "COMMIT_EDITMSG"
    message_file_path.write_text(
        "\n# Please enter the commit message for your changes.\n", encoding="utf-8"
    )
    subprocess.run(
        [sys.executable, str(HOOK_ENTRYPOINT_PATH), str(message_file_path)],
        cwd=repository,
        env=agent_session_environment(),
        check=False,
    )
    assert "Agent-Resume" not in message_file_path.read_text(encoding="utf-8")


def test_a_broken_provenance_import_never_blocks_a_commit(repository, tmp_path):
    message_file_path = tmp_path / "COMMIT_EDITMSG"
    message_file_path.write_text("feat: unaffected\n", encoding="utf-8")
    hook_run = subprocess.run(
        [sys.executable, str(HOOK_ENTRYPOINT_PATH), str(message_file_path)],
        cwd=repository,
        env=agent_session_environment() | {"PYTHONPATH": str(tmp_path)},
        check=False,
        capture_output=True,
        text=True,
    )
    assert hook_run.returncode == 0
    assert message_file_path.read_text(encoding="utf-8") == "feat: unaffected\n"
