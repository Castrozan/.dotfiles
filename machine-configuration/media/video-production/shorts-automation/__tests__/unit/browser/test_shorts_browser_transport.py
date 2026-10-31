import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from shorts_browser_pages.transport import create_page


def test_blank_page_creation_uses_current_session_and_returns_target(monkeypatch):
    run = Mock(
        return_value=SimpleNamespace(
            stdout=json.dumps({"ok": True, "data": {"page": "owned-tab"}})
        )
    )
    monkeypatch.setattr("shorts_browser_pages.transport.subprocess.run", run)
    command = ["opencli", "browser", "--session", "current-run"]
    assert create_page(command, "/owned/profile") == "owned-tab"
    assert run.call_args.args[0] == [*command, "tab", "new"]


def test_failed_creation_is_not_retried(monkeypatch):
    run = Mock(side_effect=subprocess.CalledProcessError(1, "opencli"))
    monkeypatch.setattr("shorts_browser_pages.transport.subprocess.run", run)
    with pytest.raises(subprocess.CalledProcessError):
        create_page(
            ["opencli", "browser", "--session", "current-run"], "/owned/profile"
        )
    run.assert_called_once()
