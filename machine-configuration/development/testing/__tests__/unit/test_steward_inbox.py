import json

import steward_inbox

SENDER = "nightly-deep-tiers"


def test_a_message_lands_in_the_inbox_in_the_steward_msg_shape(tmp_path, monkeypatch):
    workspace = tmp_path / "steward"
    workspace.mkdir()
    monkeypatch.setenv("STEWARD_WORKSPACE_DIR", str(workspace))

    message_file = steward_inbox.leave_message_in_the_steward_inbox(
        SENDER, "the night failed"
    )

    assert message_file.parent == workspace / "inbox"
    assert message_file.name.endswith(f"-from-{SENDER}.json")
    message = json.loads(message_file.read_text())
    assert isinstance(message["sent_unix"], int)
    assert message == {
        "from": SENDER,
        "to": "steward",
        "sent_unix": message["sent_unix"],
        "text": "the night failed",
    }


def test_no_steward_workspace_means_no_message_and_no_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("STEWARD_WORKSPACE_DIR", str(tmp_path / "absent"))

    assert steward_inbox.leave_message_in_the_steward_inbox(SENDER, "lost") is None
    assert not (tmp_path / "absent").exists()
