import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from container_configuration import ContainerPolicy
from container_leases import project_lock, record_use
from devenv_container import collect, execute


def prepare(tmp_path):
    workspace = tmp_path / "repo"
    project_directory = workspace / "project"
    project_directory.mkdir(parents=True)
    (project_directory / "devenv.nix").write_text("{}")
    policy = ContainerPolicy(
        str(workspace),
        str(tmp_path / "state"),
        "/image",
        True,
        "devenv",
        2,
        4,
        32,
        2,
        3 * 1024**3,
        512,
        600,
        28800,
        300,
    )
    project = policy.project(project_directory)
    project.state_directory.mkdir(parents=True)
    project.compose_path.write_text("{}")
    (project.state_directory / "project.json").write_text(
        json.dumps(
            {
                "directory": str(project.directory),
                "last_used": 1,
            }
        )
    )
    return policy, project


def test_stop_orphaned_container_and_release_virtual_machine(tmp_path):
    policy, project = prepare(tmp_path)
    runtime = Mock()
    runtime.project_running.return_value = True
    collect(policy, runtime)
    runtime.stop_project.assert_called_once_with(project)
    runtime.stop_machine.assert_called_once()


def test_preserve_an_active_client_even_if_the_last_use_is_old(tmp_path):
    policy, project = prepare(tmp_path)
    runtime = Mock()
    with project_lock(project, "clients", exclusive=False):
        collect(policy, runtime)
    runtime.stop_project.assert_not_called()
    runtime.stop_machine.assert_not_called()


def test_retain_recently_used_container_and_virtual_machine(tmp_path):
    policy, project = prepare(tmp_path)
    runtime = Mock()
    runtime.project_running.return_value = True
    record_use(project)
    collect(policy, runtime)
    runtime.stop_project.assert_not_called()
    runtime.stop_machine.assert_not_called()


def test_do_not_start_a_dormant_virtual_machine_to_collect_it(tmp_path):
    policy, _ = prepare(tmp_path)
    runtime = Mock()
    runtime.machine_running.return_value = False
    collect(policy, runtime)
    runtime.stop_project.assert_not_called()
    runtime.stop_machine.assert_not_called()


def test_record_idle_time_even_when_command_execution_fails(tmp_path):
    policy, project = prepare(tmp_path)
    runtime = Mock()
    runtime.execute.side_effect = RuntimeError("failed")
    try:
        execute(policy, runtime, project, ["false"], 600, False)
    except RuntimeError:
        pass
    state = json.loads((Path(project.state_directory) / "project.json").read_text())
    assert state["last_used"] > 1


def test_preserve_active_client_when_project_configuration_is_removed(tmp_path):
    policy, project = prepare(tmp_path)
    runtime = Mock()
    (project.directory / "devenv.nix").unlink()
    with project_lock(project, "clients", exclusive=False):
        collect(policy, runtime)
    runtime.stop_project.assert_not_called()
    runtime.stop_machine.assert_not_called()


def test_failed_start_without_compose_configuration_can_release_machine(tmp_path):
    policy, project = prepare(tmp_path)
    runtime = Mock()
    project.compose_path.unlink()
    collect(policy, runtime)
    runtime.stop_project.assert_not_called()
    runtime.stop_machine.assert_called_once()


def test_reject_a_second_checkout_that_would_overbook_the_budget(tmp_path):
    policy, existing = prepare(tmp_path)
    project_directory = Path(policy.workspace_root) / "second"
    project_directory.mkdir()
    (project_directory / "devenv.nix").write_text("{}")
    project = policy.project(project_directory)
    runtime = Mock()
    runtime.project_running.return_value = True
    with pytest.raises(ValueError, match="budget is occupied"):
        execute(policy, runtime, project, ["true"], 600, False)
    runtime.project_running.assert_called_once_with(existing)
    runtime.start_project.assert_not_called()
    runtime.execute.assert_not_called()
