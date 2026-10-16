"""Synthetic fleet inventories and transport; no live peer calls."""

import json
import pytest
from a2a_cli.fleet import operations
from a2a_cli.fleet.registry import Registry, DispatchIntent, Observation


@pytest.fixture
def registry(tmp_path):
    import itertools

    ticks = itertools.count(1000000)
    registry = Registry(tmp_path / "registry.sqlite3", clock=lambda: next(ticks) / 1000)
    registry.confirm_host("test-host", "local", "fixture:host-confirmed")
    yield registry
    registry.close()


def inventory(session="conversation-1", state="idle", name="peer"):
    return (
        {name: {"name": name, "paneId": "w1:p1", "harness": "codex"}},
        {
            "result": {
                "snapshot": {
                    "version": "fixture-0.9.1",
                    "protocol": 1,
                    "panes": [],
                    "tabs": [],
                    "workspaces": [],
                    "layouts": [],
                    "agents": [
                        {
                            "pane_id": "w1:p1",
                            "agent": "codex",
                            "agent_status": state,
                            "interactive_ready": True,
                            "agent_session": {"kind": "id", "value": session},
                            "tab_id": "t1",
                            "workspace_id": "w1",
                        }
                    ],
                }
            }
        },
    )


def empty_snapshot():
    snapshot = inventory()[1]
    snapshot["result"]["snapshot"]["agents"] = []
    return snapshot


def observe(registry, at=999, **kwargs):
    return registry.ingest(
        "test-host", Observation(*inventory(**kwargs), at, "fixture:snapshot", "live")
    )


class FakeTransport:
    def __init__(
        self,
        session="conversation-1",
        state="idle",
        task_state="working",
        fail_send=False,
    ):
        self.calls = []
        self.session = session
        self.state = state
        self.task_state = task_state
        self.fail_send = fail_send

    def __call__(self, host, command, timeout):
        self.calls.append(command)
        assert timeout <= 10
        directory, snapshot = inventory(session=self.session, state=self.state)
        if command[:2] == ["a2a", "list"]:
            return json.dumps(directory)
        if command[:3] == ["herdr", "api", "snapshot"]:
            return json.dumps(snapshot)
        if command[:2] == ["a2a", "send"]:
            if self.fail_send:
                raise operations.ObservationError("unreachable")
            return "remote-task-1\n"
        if command[:2] == ["a2a", "status"]:
            return json.dumps(
                {
                    "id": "remote-task-1",
                    "state": self.task_state,
                    "output": "sensitive output deliberately never retained",
                }
            )
        raise AssertionError(command)


def send(registry, transport, request="intent-1", **kwargs):
    return operations.dispatch(
        registry,
        DispatchIntent(
            request,
            "test-host",
            "w1:p1",
            "conversation-1",
            "dot",
            "task:review",
            kwargs.get("prompt", "Read the approved task brief."),
        ),
        transport,
    )
