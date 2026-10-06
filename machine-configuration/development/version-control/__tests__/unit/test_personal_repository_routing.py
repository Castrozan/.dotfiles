import json
import os
import subprocess
from pathlib import Path

import pytest


ROUTING_SOURCE = Path(__file__).resolve().parents[2] / "personal-repository-routing.nix"
PERSONAL_REPOSITORIES = (
    (".dotfiles", "dotfiles"),
    ("dotfiles-private", "dotfiles-private"),
    ("zanoni-system", "zanoni-system"),
)
REPOSITORY_URLS = [
    (source, github_target, gitlab_target)
    for github_repository, gitlab_repository in PERSONAL_REPOSITORIES
    for github_target, gitlab_target in [
        (
            f"git@github.com:Castrozan/{github_repository}.git",
            f"git@gitlab.com:Castrozan/{gitlab_repository}.git",
        )
    ]
    for source in (
        github_target,
        gitlab_target,
        f"https://github.com/Castrozan/{github_repository}.git",
        f"https://gitlab.com/Castrozan/{gitlab_repository}.git",
    )
]
REPOSITORY_URLS += [
    (source, source, source)
    for source in (
        "git@gitlab.betha.cloud:team/project.git",
        "git@gitlab.com:another-owner/project.git",
    )
]


@pytest.fixture(params=("github", "gitlab"))
def native_git_routing(request, tmp_path):
    evaluation = subprocess.run(
        [
            "nix",
            "eval",
            "--json",
            "--file",
            str(ROUTING_SOURCE),
            "--apply",
            f'routing: routing "{request.param}"',
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    configuration = tmp_path / "gitconfig"
    environment = os.environ | {
        "GIT_CONFIG_GLOBAL": str(configuration),
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True, timeout=5)
    for target, settings in json.loads(evaluation.stdout).items():
        for alias in settings["insteadOf"]:
            subprocess.run(
                [
                    "git",
                    "config",
                    "--file",
                    str(configuration),
                    "--add",
                    f"url.{target}.insteadOf",
                    alias,
                ],
                env=environment,
                check=True,
                timeout=5,
            )
    return request.param, tmp_path, environment


@pytest.mark.parametrize("source,github_target,gitlab_target", REPOSITORY_URLS)
def test_native_git_routes_only_the_personal_repositories(
    native_git_routing, source, github_target, gitlab_target
):
    forge, repository, environment = native_git_routing
    subprocess.run(
        ["git", "remote", "add", "probe", source],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    resolution = subprocess.run(
        ["git", "remote", "get-url", "probe"],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    assert (
        resolution.stdout.strip()
        == {
            "github": github_target,
            "gitlab": gitlab_target,
        }[forge]
    )
