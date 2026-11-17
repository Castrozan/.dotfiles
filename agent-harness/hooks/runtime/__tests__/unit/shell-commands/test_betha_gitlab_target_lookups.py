import subprocess

import pytest
from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS
from merge_request_target_test_support import BETHA_GITLAB_HOST, betha_gitlab_target


def checkout_with_remotes(directory, remote_locations_by_name):
    subprocess.run(
        ["git", "init", "--quiet", str(directory)],
        check=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    )
    for remote_name, remote_location in remote_locations_by_name.items():
        subprocess.run(
            [
                "git",
                "-C",
                str(directory),
                "remote",
                "add",
                remote_name,
                remote_location,
            ],
            check=True,
            timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
        )
    return str(directory)


def test_reads_every_remote_location_of_a_checkout(tmp_path):
    checkout = checkout_with_remotes(
        tmp_path,
        {
            "origin": f"git@{BETHA_GITLAB_HOST}:group/project.git",
            "mirror": "https://github.com/owner/project.git",
        },
    )
    assert betha_gitlab_target.remote_locations_of(checkout) == {
        f"git@{BETHA_GITLAB_HOST}:group/project.git",
        "https://github.com/owner/project.git",
    }


def test_reads_a_remote_location_the_way_git_rewrites_it(tmp_path):
    checkout = checkout_with_remotes(
        tmp_path, {"origin": "https://github.com/owner/project.git"}
    )
    subprocess.run(
        [
            "git",
            "-C",
            checkout,
            "config",
            f"url.https://{BETHA_GITLAB_HOST}/group/.insteadOf",
            "https://github.com/owner/",
        ],
        check=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    )
    assert betha_gitlab_target.remote_locations_of(checkout) == {
        f"https://{BETHA_GITLAB_HOST}/group/project.git"
    }


def test_reads_the_remotes_from_a_directory_below_the_checkout_root(tmp_path):
    checkout_with_remotes(tmp_path, {"origin": "https://gitlab.com/owner/project.git"})
    nested_directory = tmp_path / "source" / "module"
    nested_directory.mkdir(parents=True)
    assert betha_gitlab_target.remote_locations_of(str(nested_directory)) == {
        "https://gitlab.com/owner/project.git"
    }


def test_a_checkout_without_remotes_has_no_remote_location(tmp_path):
    assert (
        betha_gitlab_target.remote_locations_of(checkout_with_remotes(tmp_path, {}))
        == set()
    )


def test_a_directory_that_does_not_exist_has_no_remote_location(tmp_path):
    assert betha_gitlab_target.remote_locations_of(str(tmp_path / "removed")) == set()


@pytest.mark.parametrize(
    "lookup_failure",
    [FileNotFoundError("git"), subprocess.TimeoutExpired("git", 5)],
)
def test_a_lookup_that_cannot_run_reads_as_no_answer(monkeypatch, lookup_failure):
    def failing_run(*_arguments, **_options):
        raise lookup_failure

    monkeypatch.setattr(subprocess, "run", failing_run)
    assert betha_gitlab_target.remote_locations_of("/anywhere") == set()
    assert betha_gitlab_target.ssh_configured_host("work-gitlab") == "work-gitlab"
    assert betha_gitlab_target.glab_default_host() == ""


def test_a_lookup_that_exits_with_an_error_reads_as_no_answer(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **_options: subprocess.CompletedProcess(
            command, 1, stdout="hostname misleading.example.com\n"
        ),
    )
    assert betha_gitlab_target.ssh_configured_host("work-gitlab") == "work-gitlab"


def test_resolves_an_ssh_alias_to_the_host_ssh_would_dial(monkeypatch):
    asked_commands = []

    def answering_run(command, **_options):
        asked_commands.append(command)
        return subprocess.CompletedProcess(
            command, 0, stdout=f"user git\nhostname {BETHA_GITLAB_HOST.upper()}\n"
        )

    monkeypatch.setattr(subprocess, "run", answering_run)
    assert betha_gitlab_target.ssh_configured_host("work-gitlab") == BETHA_GITLAB_HOST
    assert asked_commands == [["ssh", "-G", "--", "work-gitlab"]]


def test_a_host_written_like_an_option_reaches_ssh_as_a_host(monkeypatch):
    asked_commands = []

    def answering_run(command, **_options):
        asked_commands.append(command)
        return subprocess.CompletedProcess(command, 255, stdout="")

    monkeypatch.setattr(subprocess, "run", answering_run)
    betha_gitlab_target.ssh_configured_host("-oproxycommand=touch-pwned")
    assert asked_commands[0][:3] == ["ssh", "-G", "--"]
