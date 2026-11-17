import pytest
from merge_request_target_test_support import (
    BETHA_CHECKOUT,
    BETHA_GITLAB_HOST,
    DIRECTORY_OUTSIDE_ANY_CHECKOUT,
    GITHUB_CHECKOUT,
    OTHER_GITLAB_CHECKOUT,
    SSH_ALIASED_BETHA_CHECKOUT,
    assert_denied,
    guard,
    install_machine_the_guard_looks_at,
)

UNASSIGNED_GLAB_CREATIONS = (
    "glab mr create --fill --yes",
    "glab api -X POST projects/7/merge_requests -f source_branch=feature",
)

CHECKOUTS_THAT_ARE_NOT_BETHA = (
    GITHUB_CHECKOUT,
    OTHER_GITLAB_CHECKOUT,
    DIRECTORY_OUTSIDE_ANY_CHECKOUT,
)

COMMANDS_NAMING_THE_BETHA_HOST = (
    f"GITLAB_HOST={BETHA_GITLAB_HOST} glab mr create --fill --yes",
    f"GL_HOST={BETHA_GITLAB_HOST} glab mr create --fill --yes",
    f"GITLAB_HOST=https://{BETHA_GITLAB_HOST} rtk glab mr create --fill",
    f"env GITLAB_HOST={BETHA_GITLAB_HOST} glab mr create --fill",
    f"export GITLAB_HOST={BETHA_GITLAB_HOST}; glab mr create --fill",
    f"glab mr create --fill -R https://{BETHA_GITLAB_HOST}/group/project",
    f"glab mr create --fill --repo=git@{BETHA_GITLAB_HOST}:group/project.git",
    f"glab -R ssh://git@{BETHA_GITLAB_HOST}/group/project.git mr new --fill",
    f"glab api --hostname {BETHA_GITLAB_HOST} -X POST projects/7/merge_requests "
    "-f source_branch=feature",
    f"glab api -X POST https://{BETHA_GITLAB_HOST}/api/v4/projects/7/merge_requests "
    "-f source_branch=feature",
    f'curl -sS -X POST -H "PRIVATE-TOKEN: $TOKEN" '
    f'"https://{BETHA_GITLAB_HOST}/api/v4/projects/7/merge_requests" '
    '--data "source_branch=feature"',
    f"curl -X POST -d source_branch=feature "
    f"https://oauth2:$TOKEN@{BETHA_GITLAB_HOST.upper()}/api/v4/projects/7/merge_requests",
    f"cd {BETHA_CHECKOUT} && glab mr create --fill --yes",
    f"(cd {BETHA_CHECKOUT}; glab mr create --fill --yes)",
    "cd /checkouts && cd betha-project && glab mr create --fill --yes",
)

COMMANDS_NAMING_ANOTHER_HOST = (
    "GITLAB_HOST=gitlab.example.com glab mr create --fill --yes",
    "GL_HOST=https://gitlab.example.com glab mr create --fill --yes",
    "export GITLAB_HOST=gitlab.example.com && glab mr create --fill",
    "glab mr create --fill -R https://gitlab.com/owner/project",
    "glab mr create --fill --repo git@github.com:owner/project.git",
    "glab api --hostname gitlab.com -X POST projects/7/merge_requests "
    "-f source_branch=feature",
    "glab api -X POST https://gitlab.example.com/api/v4/projects/7/merge_requests "
    "-f source_branch=feature",
    "curl -X POST -d source_branch=feature "
    "https://gitlab.example.com/api/v4/projects/7/merge_requests",
    f"cd {GITHUB_CHECKOUT} && glab mr create --fill --yes",
    f"cd {OTHER_GITLAB_CHECKOUT}; glab mr create --fill --yes",
)

COMMANDS_WHOSE_TARGET_CANNOT_BE_READ = (
    'curl -X POST -d source_branch=feature "$GITLAB_URL/api/v4/projects/7/merge_requests"',
    'curl -X POST -d source_branch=feature "https://$GITLAB_HOST/api/v4/projects/7/merge_requests"',
    'GITLAB_HOST="$WORK_GITLAB" glab mr create --fill --yes',
    'glab mr create --fill -R "$REPOSITORY_URL"',
    'cd "$PROJECT_DIRECTORY" && glab mr create --fill --yes',
    "cd /checkouts/removed-project && glab mr create --fill --yes",
)


@pytest.fixture(autouse=True)
def machine(monkeypatch):
    return install_machine_the_guard_looks_at(monkeypatch)


@pytest.mark.parametrize("command", UNASSIGNED_GLAB_CREATIONS)
@pytest.mark.parametrize("betha_checkout", [BETHA_CHECKOUT, SSH_ALIASED_BETHA_CHECKOUT])
def test_denies_an_unassigned_creation_in_a_betha_checkout(command, betha_checkout):
    assert_denied(guard(command, betha_checkout), command)


@pytest.mark.parametrize("command", UNASSIGNED_GLAB_CREATIONS)
@pytest.mark.parametrize("checkout", CHECKOUTS_THAT_ARE_NOT_BETHA)
def test_allows_an_unassigned_creation_in_any_other_directory(command, checkout):
    assert guard(command, checkout) is None, command


@pytest.mark.parametrize("command", COMMANDS_NAMING_THE_BETHA_HOST)
@pytest.mark.parametrize("checkout", CHECKOUTS_THAT_ARE_NOT_BETHA)
def test_denies_a_creation_that_names_the_betha_host_from_anywhere(command, checkout):
    assert_denied(guard(command, checkout), command)


@pytest.mark.parametrize("command", COMMANDS_NAMING_ANOTHER_HOST)
def test_allows_a_creation_that_names_another_host_from_a_betha_checkout(command):
    assert guard(command, BETHA_CHECKOUT) is None, command


@pytest.mark.parametrize("command", COMMANDS_WHOSE_TARGET_CANNOT_BE_READ)
def test_allows_a_creation_whose_target_cannot_be_read(command):
    assert guard(command, GITHUB_CHECKOUT) is None, command


@pytest.mark.parametrize(
    "command",
    [
        "gh pr create --fill",
        "gh pr new --base main --head feature --title thing",
        f"GITLAB_HOST={BETHA_GITLAB_HOST} gh pr create --fill",
    ],
)
def test_never_denies_a_github_pull_request(command):
    assert guard(command, BETHA_CHECKOUT) is None, command


def test_the_denial_names_betha_so_the_reader_knows_why_it_fired():
    result = guard("glab mr create --fill --yes", BETHA_CHECKOUT)
    assert "Betha" in result.reason
    assert len(result.reason) <= 300
