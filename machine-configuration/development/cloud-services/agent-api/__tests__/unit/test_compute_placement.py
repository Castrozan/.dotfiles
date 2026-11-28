import json
import shlex
import uuid

import pytest
from hypothesis import given
from hypothesis import strategies as st

from agent_api.contract import CapabilityError, OperationRequest
from agent_api.directives import DirectiveStore
from agent_api.inventory import INVENTORY_VARIABLE
from agent_api.providers.host_transport import job_command
from agent_api.service import CapabilityService

INVENTORY = {
    "self": "kira",
    "hosts": [
        {"name": "kira", "trust": "owned"},
        {"name": "alpha", "trust": "owned", "ssh_alias": "alpha-alias"},
        {"name": "beta", "trust": "rented"},
        {"name": "gamma", "trust": "owned"},
    ],
}
COMMAND_ARGUMENTS = st.lists(
    st.text(st.characters(codec="utf-8", exclude_characters="\x00"))
)


class RecordingExecutor:
    def __init__(self):
        self.calls = 0

    def execute(self, directory, timeout_seconds):
        self.calls += 1
        return {}


@pytest.fixture(autouse=True)
def inventory(tmp_path, monkeypatch):
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(INVENTORY))
    monkeypatch.setenv(INVENTORY_VARIABLE, str(path))


def test_submit_without_host_runs_where_placement_points_and_conflicts_once_it_moves(
    tmp_path,
):
    state_directory = tmp_path / "state"
    executor = RecordingExecutor()
    service = CapabilityService(state_directory, executor)
    operation_id = str(uuid.uuid4())
    request = OperationRequest("compute.submit", {"command": ["true"]})
    DirectiveStore(state_directory).direct("compute.placement", "beta", False)
    service.run(operation_id, request)
    retained = json.loads((state_directory / operation_id / "request.json").read_text())
    assert retained["request"]["input"]["host"] == "beta"
    DirectiveStore(state_directory).direct("compute.placement", "alpha", False)
    with pytest.raises(CapabilityError, match="operation_conflict"):
        service.run(operation_id, request)
    assert executor.calls == 1


@given(COMMAND_ARGUMENTS)
def test_remote_job_command_splits_back_into_the_program_and_exactly_the_given_arguments(
    arguments,
):
    entry = {"transport": "ssh", "ssh_alias": "alpha-alias"}
    assert shlex.split(job_command(entry, arguments)[-1]) == [
        "agent-api-job",
        *arguments,
    ]


def test_direct_pushes_the_choice_to_owned_ssh_hosts_and_reports_a_failed_host(
    tmp_path, monkeypatch
):
    commands = []

    def record(command, stdin=None, stdout=None):
        commands.append(command)
        if command[5] == "gamma":
            raise CapabilityError("host_unavailable")

    monkeypatch.setattr("agent_api.directives.run_on_host", record)
    store = DirectiveStore(tmp_path / "state")
    directed = store.direct("compute.placement", "alpha")
    assert directed["propagated"] == {"alpha": True, "gamma": False}
    assert [command[5] for command in commands] == ["alpha-alias", "gamma"]
    assert {command[-1] for command in commands} == {
        "agent-api direct compute.placement alpha --no-propagate"
    }
    assert store.target("compute.placement") == "alpha"


def test_guidance_appears_only_when_placement_names_another_machine(tmp_path):
    store = DirectiveStore(tmp_path / "state")
    assert store.guidance_lines() == []
    store.direct("compute.placement", "kira", False)
    assert store.guidance_lines() == []
    store.direct("compute.placement", "alpha", False)
    assert store.guidance_lines() == [
        "Compute placement is alpha: submit long or heavy commands as agent-api compute jobs so they run on alpha."
    ]
