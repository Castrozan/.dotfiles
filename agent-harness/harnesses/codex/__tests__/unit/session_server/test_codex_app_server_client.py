import json
import sys
from types import ModuleType
from unittest.mock import Mock

import pytest

from codex_app_server_client import (
    CodexAppServerClient,
    CodexAppServerError,
    CodexThreadTitle,
)


@pytest.fixture
def connection(monkeypatch):
    connection = Mock()
    connection.recv.side_effect = [json.dumps({"id": 1, "result": {}})]
    client_module = ModuleType("websockets.sync.client")
    client_module.unix_connect = Mock(return_value=connection)
    monkeypatch.setitem(sys.modules, "websockets.sync.client", client_module)
    return connection


def sent_messages(connection):
    return [json.loads(call.args[0]) for call in connection.send.call_args_list]


def test_connection_initializes_and_reads_a_thread_without_loading_its_turns(
    connection,
):
    with CodexAppServerClient("/private/socket") as client:
        connection.recv.side_effect = [
            json.dumps({"method": "thread/status/changed", "params": {}}),
            json.dumps({"id": 900, "result": {}}),
            json.dumps(
                {
                    "id": 2,
                    "result": {
                        "thread": {
                            "name": "Fix footer",
                            "preview": "Fix terminal title",
                        }
                    },
                }
            ),
        ]
        assert client.thread_title("thread-123") == CodexThreadTitle(
            "Fix footer", "Fix terminal title"
        )
    messages = sent_messages(connection)
    assert messages[0]["method"] == "initialize"
    assert messages[1] == {"method": "initialized", "params": {}}
    assert messages[2] == {
        "id": 2,
        "method": "thread/read",
        "params": {"threadId": "thread-123", "includeTurns": False},
    }
    connection.close.assert_called_once()


def test_setting_a_name_uses_the_loaded_thread_identifier(connection):
    with CodexAppServerClient("/private/socket") as client:
        connection.recv.side_effect = [json.dumps({"id": 2, "result": {}})]
        client.set_thread_name("thread-123", "BB | Fix footer")
    assert sent_messages(connection)[-1] == {
        "id": 2,
        "method": "thread/name/set",
        "params": {"threadId": "thread-123", "name": "BB | Fix footer"},
    }


def test_rpc_failure_closes_the_connection(connection):
    with CodexAppServerClient("/private/socket") as client:
        connection.recv.side_effect = [
            json.dumps({"id": 2, "error": {"message": "thread unavailable"}})
        ]
        with pytest.raises(CodexAppServerError, match="thread unavailable"):
            client.thread_title("thread-123")
    connection.close.assert_called_once()


def test_failed_initialization_releases_the_socket(connection):
    connection.recv.side_effect = [
        json.dumps({"id": 1, "error": {"message": "denied"}})
    ]
    with pytest.raises(CodexAppServerError, match="denied"):
        CodexAppServerClient("/private/socket")
    connection.close.assert_called_once()


def test_notification_stream_cannot_extend_the_naming_deadline(connection, monkeypatch):
    clock = Mock(side_effect=[0.0, 0.1, 0.2, 0.8, 1.1])
    monkeypatch.setattr("codex_app_server_client.time.monotonic", clock)
    with CodexAppServerClient("/private/socket", timeout_seconds=1.0) as client:
        connection.recv.side_effect = [
            json.dumps({"method": "thread/status/changed", "params": {}})
        ] * 4
        with pytest.raises(TimeoutError):
            client.thread_title("thread-123")
    connection.close.assert_called_once()


@pytest.mark.parametrize(
    "thread,error",
    [
        ({"name": 123, "preview": "Title"}, "invalid thread name"),
        ({"name": None, "preview": None}, "invalid thread preview"),
    ],
)
def test_invalid_thread_title_is_rejected(connection, thread, error):
    with CodexAppServerClient("/private/socket") as client:
        connection.recv.side_effect = [
            json.dumps({"id": 2, "result": {"thread": thread}})
        ]
        with pytest.raises(CodexAppServerError, match=error):
            client.thread_title("thread-123")
    connection.close.assert_called_once()
