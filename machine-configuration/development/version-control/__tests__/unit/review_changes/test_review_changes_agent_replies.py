import json
import sqlite3
from contextlib import closing
from unittest.mock import MagicMock, patch

import pytest

import agent_replies

FIRST_LINK = "https://gitlab.example/group/project/-/merge_requests/1"
LATEST_LINK = "https://github.com/owner/repo/pull/2"


def write_lines(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(entry) + "\n" for entry in entries))


def claude_entry(entry_type, text, sidechain=False):
    return {
        "type": entry_type,
        "isSidechain": sidechain,
        "message": {"content": [{"type": "text", "text": text}]},
    }


def codex_entry(role, text):
    return {
        "type": "response_item",
        "payload": {
            "role": role,
            "content": [{"type": "output_text", "text": text}],
        },
    }


@pytest.fixture
def herdr_pane(monkeypatch):
    monkeypatch.setenv("HERDR_ACTIVE_PANE_ID", "w1:p2")

    def answer_pane(agent, session_identifier, directory="/work/my.project"):
        pane = {
            "pane_id": "w1:p2",
            "cwd": directory,
            "agent_session": {
                "agent": agent,
                "kind": "id",
                "value": session_identifier,
            },
        }
        return MagicMock(returncode=0, stdout=json.dumps({"result": {"pane": pane}}))

    return answer_pane


def test_claude_reply_with_a_link_is_found_in_the_transcript_named_after_the_cwd(
    tmp_path, monkeypatch, herdr_pane
):
    monkeypatch.setattr(agent_replies, "CLAUDE_PROJECTS_DIRECTORY", tmp_path)
    write_lines(
        tmp_path / "-work-my-project" / "session-1.jsonl",
        [
            claude_entry("assistant", f"first {FIRST_LINK}"),
            claude_entry("user", "https://github.com/user/typed/pull/9"),
            claude_entry("assistant", f"subagent {FIRST_LINK}", sidechain=True),
            claude_entry("assistant", f"latest {LATEST_LINK} and {FIRST_LINK}"),
            claude_entry("assistant", "no link here"),
        ],
    )
    with patch(
        "agent_replies.run_command", return_value=herdr_pane("claude", "session-1")
    ):
        detected_request = agent_replies.latest_request_link_in_active_agent()
    assert detected_request.reference == "owner/repo#2"


def test_claude_reply_with_string_content_is_found(tmp_path, monkeypatch, herdr_pane):
    monkeypatch.setattr(agent_replies, "CLAUDE_PROJECTS_DIRECTORY", tmp_path)
    write_lines(
        tmp_path / "-work-my-project" / "session-1.jsonl",
        [
            {
                "type": "assistant",
                "isSidechain": False,
                "message": {"content": FIRST_LINK},
            }
        ],
    )
    with patch(
        "agent_replies.run_command", return_value=herdr_pane("claude", "session-1")
    ):
        detected_request = agent_replies.latest_request_link_in_active_agent()
    assert detected_request.reference == "group/project!1"


def test_codex_reply_is_found_in_its_rollout(tmp_path, monkeypatch, herdr_pane):
    monkeypatch.setattr(agent_replies, "CODEX_SESSIONS_DIRECTORY", tmp_path)
    write_lines(
        tmp_path / "2026" / "10" / "24" / "rollout-2026-10-24T03-13-54-thread-7.jsonl",
        [codex_entry("assistant", FIRST_LINK), codex_entry("user", LATEST_LINK)],
    )
    with patch(
        "agent_replies.run_command", return_value=herdr_pane("codex", "thread-7")
    ):
        detected_request = agent_replies.latest_request_link_in_active_agent()
    assert detected_request.reference == "group/project!1"


def test_opencode_reply_is_found_in_its_database(tmp_path, monkeypatch, herdr_pane):
    database_path = tmp_path / "opencode.db"
    monkeypatch.setattr(agent_replies, "OPENCODE_DATABASE", database_path)
    with closing(sqlite3.connect(database_path)) as database:
        database.executescript(
            "create table message (id text, session_id text, time_created integer,"
            " data text);"
            "create table part (id text, message_id text, session_id text,"
            " time_created integer, data text);"
        )
        for message_identifier, role, created, text in [
            ("m1", "assistant", 1, LATEST_LINK),
            ("m2", "assistant", 2, FIRST_LINK),
            ("m3", "user", 3, LATEST_LINK),
        ]:
            database.execute(
                "insert into message values (?, 'ses_1', ?, ?)",
                (message_identifier, created, json.dumps({"role": role})),
            )
            database.execute(
                "insert into part values (?, ?, 'ses_1', ?, ?)",
                (
                    f"p{created}",
                    message_identifier,
                    created,
                    json.dumps({"type": "text", "text": text}),
                ),
            )
        database.commit()
    with patch(
        "agent_replies.run_command", return_value=herdr_pane("opencode", "ses_1")
    ):
        detected_request = agent_replies.latest_request_link_in_active_agent()
    assert detected_request.reference == "group/project!1"


def test_agent_without_a_readable_transcript_falls_back_to_the_screen(
    tmp_path, monkeypatch, herdr_pane
):
    monkeypatch.setattr(agent_replies, "CLAUDE_PROJECTS_DIRECTORY", tmp_path)
    screen = MagicMock(returncode=0, stdout=f"older {FIRST_LINK}\nnewer {LATEST_LINK}")
    with patch(
        "agent_replies.run_command",
        side_effect=[herdr_pane("claude", "missing"), screen],
    ) as run_command:
        detected_request = agent_replies.latest_request_link_in_active_agent()
    assert run_command.call_args.args[0][:4] == ["herdr", "pane", "read", "w1:p2"]
    assert detected_request.reference == "owner/repo#2"


def test_nothing_is_detected_outside_herdr(monkeypatch):
    monkeypatch.delenv("HERDR_ACTIVE_PANE_ID", raising=False)
    with patch("agent_replies.run_command") as run_command:
        assert agent_replies.latest_request_link_in_active_agent() is None
    run_command.assert_not_called()


def test_a_torn_transcript_line_does_not_hide_earlier_replies(
    tmp_path, monkeypatch, herdr_pane
):
    monkeypatch.setattr(agent_replies, "CLAUDE_PROJECTS_DIRECTORY", tmp_path)
    transcript = tmp_path / "-work-my-project" / "session-1.jsonl"
    write_lines(transcript, [claude_entry("assistant", FIRST_LINK)])
    with transcript.open("a") as transcript_file:
        transcript_file.write(f'{{"type": "assistant", "message": "{LATEST_LINK}\n')
    with patch(
        "agent_replies.run_command", return_value=herdr_pane("claude", "session-1")
    ):
        detected_request = agent_replies.latest_request_link_in_active_agent()
    assert detected_request.reference == "group/project!1"
