import json
import subprocess
from unittest.mock import patch

from steward_test_helpers import steward_msg


def make_configuration():
    return {
        "self": "chise",
        "remote_inbox": "clawde/steward/inbox",
        "peers": {
            "jojo": {
                "host": "100.127.240.60",
                "user": "lucas.zanoni",
                "identity_file": "~/.ssh/id_ed25519",
            },
            "rin": {
                "host": "100.98.175.77",
                "user": "lucas.zanoni",
                "identity_file": "~/.ssh/id_ed25519",
            },
        },
    }


def test_argument_parser_routes_subcommands():
    parser = steward_msg.build_argument_parser()
    assert parser.parse_args(["send", "jojo", "hello"]).peer == "jojo"
    assert parser.parse_args(["broadcast", "hi"]).text == "hi"
    assert parser.parse_args(["inbox", "--drain"]).drain is True
    assert parser.parse_args(["peers"]).handler is steward_msg.command_peers


def test_load_peers_configuration_reads_file(monkeypatch, tmp_path):
    peers_file = tmp_path / "peers.json"
    peers_file.write_text(json.dumps(make_configuration()))
    monkeypatch.setenv("STEWARD_PEERS_FILE", str(peers_file))
    assert steward_msg.load_peers_configuration()["self"] == "chise"


def test_deliver_to_unknown_peer_fails():
    ok, detail = steward_msg.deliver_to_peer(make_configuration(), "ghost", "x")
    assert ok is False
    assert "unknown peer" in detail


def test_deliver_to_peer_invokes_ssh_and_succeeds():
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch("subprocess.run", return_value=completed) as mock_run:
        ok, detail = steward_msg.deliver_to_peer(
            make_configuration(), "jojo", "fixed main"
        )
    assert ok is True
    sent_command = mock_run.call_args[0][0]
    assert sent_command[0] == "ssh"
    assert "lucas.zanoni@100.127.240.60" in sent_command


def test_deliver_to_peer_reports_ssh_failure():
    completed = subprocess.CompletedProcess(
        args=[], returncode=255, stdout="", stderr="boom"
    )
    with patch("subprocess.run", return_value=completed):
        ok, detail = steward_msg.deliver_to_peer(make_configuration(), "jojo", "x")
    assert ok is False
    assert detail == "boom"
