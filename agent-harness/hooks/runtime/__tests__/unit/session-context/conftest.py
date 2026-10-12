from unittest.mock import Mock

import pytest

import codex_servant_status_handler as status_handler
from codex_app_server_client import CodexThreadTitle


@pytest.fixture
def session_client(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.delenv("OPENCLAW_GATEWAY_PORT", raising=False)
    monkeypatch.setenv("CODEX_SESSION_SOCKET_PATH", str(tmp_path / "private.sock"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    client = Mock()
    client.thread_title.return_value = CodexThreadTitle(None, "Fix terminal title")
    connection = Mock()
    connection.return_value.__enter__ = Mock(return_value=client)
    connection.return_value.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(status_handler, "CodexAppServerClient", connection)
    return client, connection
