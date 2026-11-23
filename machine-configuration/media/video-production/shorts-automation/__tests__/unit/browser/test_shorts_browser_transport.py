import json
from types import SimpleNamespace
from unittest.mock import Mock

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
