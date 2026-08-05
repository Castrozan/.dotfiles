import pytest
from a2a_cli import peer_transport
from a2a_cli.peer_transport import (
    PeerRequestFailure,
    poll_task_until_terminal,
    read_agent_directory,
    resolve_peer_endpoint,
    submit_task_to_peer,
)

DIRECTORY_WITH_ONE_AGENT = {
    "golden": {
        "name": "golden",
        "endpoint": "http://127.0.0.1:7000/agents/golden/",
        "description": "golden",
        "harness": "claude",
        "paneId": "w1:p9",
    }
}


class TestReadingTheLiveDirectory:
    def test_the_daemon_answer_is_keyed_by_agent_name(self, monkeypatch):
        monkeypatch.setattr(
            peer_transport,
            "request_peer_json",
            lambda *_args, **_kwargs: (
                200,
                {"agents": list(DIRECTORY_WITH_ONE_AGENT.values())},
            ),
        )
        assert read_agent_directory("http://127.0.0.1:7000")["golden"][
            "harness"
        ] == "claude"

    def test_a_daemon_that_is_not_running_names_the_endpoint_it_tried(self, monkeypatch):
        def refuse(*_args, **_kwargs):
            raise PeerRequestFailure("http://127.0.0.1:7000/agents is unreachable")

        monkeypatch.setattr(peer_transport, "request_peer_json", refuse)
        with pytest.raises(PeerRequestFailure, match="127.0.0.1:7000"):
            read_agent_directory("http://127.0.0.1:7000")

    def test_a_daemon_answering_anything_but_200_is_a_failure(self, monkeypatch):
        monkeypatch.setattr(
            peer_transport,
            "request_peer_json",
            lambda *_args, **_kwargs: (503, {}),
        )
        with pytest.raises(PeerRequestFailure, match="503"):
            read_agent_directory("http://127.0.0.1:7000")


class TestEndpointResolution:
    def test_the_trailing_slash_is_stripped_so_paths_do_not_double_up(self):
        assert (
            resolve_peer_endpoint(DIRECTORY_WITH_ONE_AGENT, "golden")
            == "http://127.0.0.1:7000/agents/golden"
        )

    def test_an_unknown_agent_lists_the_agents_that_are_attached(self):
        with pytest.raises(PeerRequestFailure, match="golden"):
            resolve_peer_endpoint(DIRECTORY_WITH_ONE_AGENT, "nobody")

    def test_an_empty_directory_says_so_instead_of_listing_nothing(self):
        with pytest.raises(PeerRequestFailure, match="none attached"):
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
