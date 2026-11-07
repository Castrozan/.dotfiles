import argparse
import json
import subprocess

import pytest
from a2a_cli import peer_identity
from a2a_cli.commands import command_list
from a2a_cli.peer_identity import with_peer_identities
from a2a_cli.peer_transport import PeerRequestFailure, resolve_peer_endpoint
from catalog import select_servant_for_session

INTERACTIVE_SESSION = "a9677e22-a6ea-422a-b267-12231aed691a"
CLAWDE_SESSION = "0b7e1c1d-1f3a-4c55-9d0e-6a3f2b8c4d11"
INTERACTIVE_SERVANT = select_servant_for_session(INTERACTIVE_SESSION)["name"]

DIRECTORY = {
    "evals-hillclimb": {
        "name": "evals-hillclimb",
        "endpoint": "http://127.0.0.1:7000/agents/evals-hillclimb",
        "harness": "claude",
        "paneId": "wW:pN7",
        "description": "claude session evals-hillclimb",
    },
    "monster": {
        "name": "monster",
        "endpoint": "http://127.0.0.1:7000/agents/monster",
        "harness": "claude",
        "paneId": "wV:pF1",
        "description": "a clawde agent",
    },
    "shell-pane": {
        "name": "shell-pane",
        "endpoint": "http://127.0.0.1:7000/agents/shell-pane",
        "harness": "codex",
        "paneId": "wV:pF2",
        "description": "codex session shell-pane",
    },
}


def live_pane(pane_id, working_directory, session_identifier=None, harness="claude"):
    pane = {"pane_id": pane_id, "agent": harness, "cwd": working_directory}
    if session_identifier:
        pane["agent_session"] = {
            "agent": harness,
            "kind": "id",
            "source": f"herdr:{harness}",
            "value": session_identifier,
        }
    return pane


@pytest.fixture
def clawde_workspaces(monkeypatch, tmp_path):
    workspaces = tmp_path / "clawde"
    (workspaces / "monster").mkdir(parents=True)
    monkeypatch.setenv("CLAWDE_AGENTS_DIRECTORY", str(workspaces))
    return workspaces


@pytest.fixture
def herdr_reports(monkeypatch, clawde_workspaces):
    panes = [
        live_pane("wW:pN7", "/home/operator/.dotfiles", INTERACTIVE_SESSION),
        live_pane("wV:pF1", str(clawde_workspaces / "monster"), CLAWDE_SESSION),
        live_pane("wV:pF2", "/home/operator", harness="codex"),
    ]

    def list_panes(arguments, **options):
        assert arguments == ["herdr", "pane", "list"]
        assert options["timeout"] <= 2.0
        return subprocess.CompletedProcess(
            arguments, 0, json.dumps({"result": {"panes": panes}}), ""
        )

    monkeypatch.setattr(peer_identity.subprocess, "run", list_panes)


class TestAnnotatingTheDirectory:
    def test_an_interactive_session_carries_its_servant_and_session_id(
        self, herdr_reports
    ):
        peer = with_peer_identities(DIRECTORY)["evals-hillclimb"]
        assert peer["servant"] == INTERACTIVE_SERVANT
        assert peer["sessionId"] == INTERACTIVE_SESSION

    def test_a_clawde_agent_keeps_its_session_id_but_draws_no_servant(
        self, herdr_reports
    ):
        peer = with_peer_identities(DIRECTORY)["monster"]
        assert peer["sessionId"] == CLAWDE_SESSION
        assert "servant" not in peer

    def test_a_pane_reporting_no_session_gains_nothing(self, herdr_reports):
        assert with_peer_identities(DIRECTORY)["shell-pane"] == DIRECTORY["shell-pane"]

    def test_an_unreachable_herdr_leaves_the_directory_as_the_daemon_sent_it(
        self, monkeypatch
    ):
        def refuse(*_arguments, **_options):
            raise OSError("herdr is not installed on this host")

        monkeypatch.setattr(peer_identity.subprocess, "run", refuse)
        assert with_peer_identities(DIRECTORY) == DIRECTORY


class TestListing:
    def test_the_text_listing_shows_servant_and_session_or_a_dash(
        self, herdr_reports, capsys
    ):
        command_list(argparse.Namespace(json=False), with_peer_identities(DIRECTORY))
        rows = {
            line.split("\t")[0]: line.split("\t")
            for line in capsys.readouterr().out.splitlines()
        }
        assert rows["evals-hillclimb"][1:5] == [
            INTERACTIVE_SERVANT,
            "claude",
            "wW:pN7",
            INTERACTIVE_SESSION,
        ]
        assert rows["shell-pane"][1] == "-"
        assert rows["shell-pane"][4] == "-"

    def test_the_json_listing_carries_the_same_identity(self, herdr_reports, capsys):
        command_list(argparse.Namespace(json=True), with_peer_identities(DIRECTORY))
        listed = json.loads(capsys.readouterr().out)
        assert listed["evals-hillclimb"]["servant"] == INTERACTIVE_SERVANT
        assert listed["evals-hillclimb"]["sessionId"] == INTERACTIVE_SESSION


def peer(name, servant=None, session_identifier=None):
    entry = {
        "name": name,
        "endpoint": f"http://127.0.0.1:7000/agents/{name}",
        "paneId": f"w1:{name}",
    }
    if servant:
        entry["servant"] = servant
    if session_identifier:
        entry["sessionId"] = session_identifier
    return entry


class TestAddressingByIdentity:
    def test_a_servant_name_reaches_its_peer_whatever_its_case(self):
        directory = {"evals-hillclimb": peer("evals-hillclimb", "Iskandar")}
        assert resolve_peer_endpoint(directory, "iskandar").endswith("evals-hillclimb")

    def test_a_session_id_reaches_its_peer(self):
        directory = {
            "evals-hillclimb": peer("evals-hillclimb", "Iskandar", INTERACTIVE_SESSION)
        }
        assert resolve_peer_endpoint(directory, INTERACTIVE_SESSION).endswith(
            "evals-hillclimb"
        )

    def test_a_shared_servant_is_refused_and_every_candidate_is_named(self):
        directory = {
            "first": peer("first", "Iskandar"),
            "second": peer("second", "Iskandar"),
        }
        with pytest.raises(PeerRequestFailure, match="first.*second"):
            resolve_peer_endpoint(directory, "Iskandar")

    def test_a_peer_name_wins_over_another_peers_servant(self):
        directory = {
            "Iskandar": peer("Iskandar"),
            "evals-hillclimb": peer("evals-hillclimb", "Iskandar"),
        }
        assert resolve_peer_endpoint(directory, "Iskandar").endswith("/Iskandar")

    def test_an_unknown_target_lists_peers_with_their_servants(self):
        directory = {"evals-hillclimb": peer("evals-hillclimb", "Iskandar")}
        with pytest.raises(PeerRequestFailure, match="evals-hillclimb \\(Iskandar\\)"):
            resolve_peer_endpoint(directory, "nobody")

    def test_an_empty_target_reaches_no_peer_lacking_a_servant(self):
        directory = {"shell-pane": peer("shell-pane")}
        with pytest.raises(PeerRequestFailure, match="unknown agent"):
            resolve_peer_endpoint(directory, "")
