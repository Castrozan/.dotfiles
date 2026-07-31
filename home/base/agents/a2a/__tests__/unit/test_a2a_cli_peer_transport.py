import json

import pytest
from a2a_cli import peer_transport
from a2a_cli.peer_transport import (
    PeerRequestFailure,
    load_peer_registry,
    poll_task_until_terminal,
    resolve_peer_endpoint,
    submit_task_to_peer,
)

REGISTRY_WITH_ONE_PEER = {
    "peers": {"golden": {"endpoint": "http://127.0.0.1:7001/", "description": "golden"}}
}


def write_registry(tmp_path, payload):
    registry_path = tmp_path / "peers.json"
    registry_path.write_text(json.dumps(payload), encoding="utf-8")
    return registry_path


class TestPeerRegistryLoading:
    def test_a_missing_registry_reads_as_no_peers_rather_than_an_error(self, tmp_path):
        assert load_peer_registry(tmp_path / "absent.json") == {}

    def test_a_declared_peer_is_returned_by_name(self, tmp_path):
        registry = load_peer_registry(write_registry(tmp_path, REGISTRY_WITH_ONE_PEER))
        assert registry["golden"]["endpoint"] == "http://127.0.0.1:7001/"

    def test_an_unreadable_registry_names_the_file_it_could_not_parse(self, tmp_path):
        registry_path = tmp_path / "peers.json"
        registry_path.write_text("{not json", encoding="utf-8")
        with pytest.raises(PeerRequestFailure, match=str(registry_path)):
            load_peer_registry(registry_path)


class TestEndpointResolution:
    def test_the_trailing_slash_is_stripped_so_paths_do_not_double_up(self):
        assert (
            resolve_peer_endpoint(REGISTRY_WITH_ONE_PEER["peers"], "golden")
            == "http://127.0.0.1:7001"
        )

    def test_an_unknown_peer_lists_the_peers_that_do_exist(self):
        with pytest.raises(PeerRequestFailure, match="golden"):
            resolve_peer_endpoint(REGISTRY_WITH_ONE_PEER["peers"], "nobody")

    def test_an_empty_registry_says_so_instead_of_listing_nothing(self):
        with pytest.raises(PeerRequestFailure, match="none declared"):
            resolve_peer_endpoint({}, "nobody")


class TestTaskSubmission:
    def test_a_busy_peer_reports_the_task_that_is_holding_it(self, monkeypatch):
        monkeypatch.setattr(
            peer_transport,
            "request_peer_json",
            lambda *_args, **_kwargs: (409, {"id": "task-in-flight"}),
        )
        with pytest.raises(PeerRequestFailure, match="task-in-flight"):
            submit_task_to_peer("http://127.0.0.1:7001", "hello")

    def test_an_accepted_task_is_returned_as_submitted(self, monkeypatch):
        monkeypatch.setattr(
            peer_transport,
            "request_peer_json",
            lambda *_args, **_kwargs: (201, {"id": "task-1", "state": "working"}),
        )
        assert submit_task_to_peer("http://127.0.0.1:7001", "hello")["id"] == "task-1"

    def test_any_other_status_is_a_failure_carrying_the_status_code(self, monkeypatch):
        monkeypatch.setattr(
            peer_transport,
            "request_peer_json",
            lambda *_args, **_kwargs: (500, {"error": "internal_error"}),
        )
        with pytest.raises(PeerRequestFailure, match="500"):
            submit_task_to_peer("http://127.0.0.1:7001", "hello")


class TestPollingUntilTheTaskEnds:
    def test_polling_returns_the_task_once_it_reaches_a_terminal_state(
        self, monkeypatch
    ):
        states = iter(["working", "working", "completed"])
        monkeypatch.setattr(peer_transport, "POLL_INTERVAL_SECONDS", 0)
        monkeypatch.setattr(
            peer_transport,
            "read_task_from_peer",
            lambda *_args: {"id": "task-1", "state": next(states), "output": "done"},
        )
        finished = poll_task_until_terminal("http://127.0.0.1:7001", "task-1", 5.0)
        assert finished["state"] == "completed"

    def test_a_task_that_never_ends_points_at_the_command_that_reads_it_later(
        self, monkeypatch
    ):
        monkeypatch.setattr(peer_transport, "POLL_INTERVAL_SECONDS", 0)
        monkeypatch.setattr(
            peer_transport,
            "read_task_from_peer",
            lambda *_args: {"id": "task-1", "state": "working"},
        )
        with pytest.raises(PeerRequestFailure, match="a2a status"):
            poll_task_until_terminal("http://127.0.0.1:7001", "task-1", 0.0)
