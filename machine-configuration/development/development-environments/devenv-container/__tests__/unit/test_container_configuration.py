from pathlib import Path

import pytest

from container_configuration import ContainerPolicy, compose_configuration


@pytest.fixture
def policy(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    return ContainerPolicy(
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


def create_project(policy, name="project"):
    project = Path(policy.workspace_root) / name
    project.mkdir()
    (project / "devenv.nix").write_text("{}")
    return policy.project(project)


def test_limit_the_entire_container_without_swap_or_host_privileges(policy):
    project = create_project(policy)
    configuration = compose_configuration(policy, project)
    environment = configuration["services"]["environment"]
    assert environment["mem_limit"] == environment["memswap_limit"] == 3 * 1024**3
    assert environment["cpus"] == 2
    assert environment["pids_limit"] == 512
    assert environment["cap_drop"] == ["ALL"]
    assert environment["security_opt"] == ["no-new-privileges:true"]
    assert environment["init"] is True
    assert environment["restart"] == "no"
    assert environment["command"][3] == "28800"


def test_only_bind_the_checkout_and_preserve_separate_installation_storage(policy):
    project = create_project(policy)
    configuration = compose_configuration(policy, project)
    volumes = configuration["services"]["environment"]["volumes"]
    bind_mounts = [volume for volume in volumes if volume["type"] == "bind"]
    assert bind_mounts == [
        {
            "type": "bind",
            "source": str(project.directory),
            "target": str(project.directory),
        }
    ]
    assert configuration["volumes"]["nix"] == {}
    assert configuration["volumes"]["home"] == {}


def test_checkout_identity_survives_symlink_aliases_and_separates_workspaces(policy):
    first = create_project(policy, "first")
    alias = Path(policy.workspace_root) / "alias"
    alias.symlink_to(first.directory)
    assert policy.project(alias).identity == first.identity
    assert create_project(policy, "second").identity != first.identity


def test_reject_symlinks_escaping_the_declared_workspace(policy, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "devenv.nix").write_text("{}")
    alias = Path(policy.workspace_root) / "escape"
    alias.symlink_to(outside)
    with pytest.raises(ValueError, match="beneath"):
        policy.project(alias)


def test_reject_a_checkout_without_devenv_configuration(policy):
    directory = Path(policy.workspace_root) / "empty"
    directory.mkdir()
    with pytest.raises(ValueError, match="No devenv.nix"):
        policy.project(directory)
