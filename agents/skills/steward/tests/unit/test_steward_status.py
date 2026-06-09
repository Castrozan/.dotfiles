import json

from steward_test_helpers import steward_status


def test_self_alias_prefers_environment(monkeypatch):
    monkeypatch.setenv("STEWARD_SELF", "chise")
    assert steward_status.self_alias() == "chise"


def test_self_alias_falls_back_to_peers_file(monkeypatch, tmp_path):
    monkeypatch.delenv("STEWARD_SELF", raising=False)
    monkeypatch.setenv("STEWARD_WORKSPACE_DIR", str(tmp_path))
    (tmp_path / "peers.json").write_text(json.dumps({"self": "kira", "peers": {}}))
    assert steward_status.self_alias() == "kira"


def test_unread_inbox_lists_only_json_sorted(monkeypatch, tmp_path):
    monkeypatch.setenv("STEWARD_WORKSPACE_DIR", str(tmp_path))
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "2-from-rin.json").write_text("{}")
    (inbox / "1-from-jojo.json").write_text("{}")
    (inbox / "note.txt").write_text("ignored")
    assert steward_status.unread_inbox_messages() == [
        "1-from-jojo.json",
        "2-from-rin.json",
    ]


def test_last_validated_revision_reads_stamp(monkeypatch, tmp_path):
    monkeypatch.setenv("STEWARD_WORKSPACE_DIR", str(tmp_path))
    state = tmp_path / "state"
    state.mkdir()
    (state / "last-validated-sha").write_text("deadbeef\n")
    assert steward_status.last_validated_revision() == "deadbeef"
