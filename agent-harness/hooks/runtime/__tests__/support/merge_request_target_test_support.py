import os

from hook_module_loader import import_hyphenated_hook_module

merge_request_assignee_guard_handler = import_hyphenated_hook_module(
    "merge_request_assignee_guard_handler"
)
betha_gitlab_target = import_hyphenated_hook_module("betha_gitlab_target")

BETHA_GITLAB_HOST = betha_gitlab_target.BETHA_GITLAB_HOST
BETHA_CHECKOUT = "/checkouts/betha-project"
GITHUB_CHECKOUT = "/checkouts/github-project"
OTHER_GITLAB_CHECKOUT = "/checkouts/other-gitlab-project"
SSH_ALIASED_BETHA_CHECKOUT = "/checkouts/ssh-aliased-betha-project"
DIRECTORY_OUTSIDE_ANY_CHECKOUT = "/outside-any-checkout"
SSH_ALIAS_OF_THE_BETHA_HOST = "work-gitlab"

REMOTE_LOCATIONS_BY_CHECKOUT = {
    BETHA_CHECKOUT: {f"git@{BETHA_GITLAB_HOST}:group/project.git"},
    GITHUB_CHECKOUT: {"git@github.com:owner/project.git"},
    OTHER_GITLAB_CHECKOUT: {"https://gitlab.com/owner/project.git"},
    SSH_ALIASED_BETHA_CHECKOUT: {
        f"git@{SSH_ALIAS_OF_THE_BETHA_HOST}:group/project.git"
    },
}


class MachineTheGuardLooksAt:
    def __init__(self):
        self.remote_locations_by_directory = dict(REMOTE_LOCATIONS_BY_CHECKOUT)
        self.ssh_host_by_alias = {SSH_ALIAS_OF_THE_BETHA_HOST: BETHA_GITLAB_HOST}
        self.glab_default_host = "gitlab.com"

    def remote_locations_of(self, working_directory):
        return self.remote_locations_by_directory.get(
            os.path.normpath(working_directory), set()
        )

    def ssh_configured_host(self, written_host):
        return self.ssh_host_by_alias.get(written_host, written_host)

    def read_glab_default_host(self):
        return self.glab_default_host


def install_machine_the_guard_looks_at(monkeypatch):
    machine = MachineTheGuardLooksAt()
    for host_variable in betha_gitlab_target.GLAB_HOST_VARIABLES:
        monkeypatch.delenv(host_variable, raising=False)
    monkeypatch.setattr(
        betha_gitlab_target, "remote_locations_of", machine.remote_locations_of
    )
    monkeypatch.setattr(
        betha_gitlab_target, "ssh_configured_host", machine.ssh_configured_host
    )
    monkeypatch.setattr(
        betha_gitlab_target, "glab_default_host", machine.read_glab_default_host
    )
    return machine


def guard(command, working_directory=BETHA_CHECKOUT):
    return merge_request_assignee_guard_handler.handle(
        {
            "tool_name": "Bash",
            "cwd": working_directory,
            "tool_input": {"command": command},
        }
    )


def assert_denied(result, command):
    assert result is not None, command
    assert result.decision == "deny"
