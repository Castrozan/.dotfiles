import json
import secrets
from types import SimpleNamespace

import pytest
from shorts_browser_pages.ownership import BrowserPages


@pytest.fixture(autouse=True)
def private_browser_job_token(monkeypatch):
    token = secrets.token_urlsafe(32)
    monkeypatch.setattr("shorts_browser_pages.transport.job_token", lambda scope: token)
    return token


@pytest.fixture
def browser_pages(tmp_path, monkeypatch):
    targets = {"operator-tab": {"id": "operator-tab", "url": "https://example.com"}}
    commands = []

    def execute(arguments, **options):
        command = arguments[4:]
        commands.append(command)
        if command[:2] == ["tab", "list"]:
            return SimpleNamespace(
                stdout=json.dumps(
                    {
                        "ok": True,
                        "data": [
                            dict(target, page=target["id"])
                            for target in targets.values()
                        ],
                    }
                )
            )
        if command[:2] == ["tab", "close"]:
            del targets[command[2]]
            return SimpleNamespace(stdout='{"ok":true,"data":{}}')
        raise AssertionError(command)

    def create(server, scope):
        identifier = f"owned-{len(targets)}"
        targets[identifier] = {"id": identifier, "url": "about:blank"}
        commands.append(["create"])
        return identifier

    monkeypatch.setattr("shorts_browser_pages.transport.subprocess.run", execute)
    monkeypatch.setattr("shorts_browser_pages.ownership.create_page", create)
    pages = BrowserPages(
        tmp_path,
        "morning",
        ["opencli", "browser", "--session", "run"],
        "instance",
        "/owned/profile",
    )
    pages.begin()
    return pages, targets, commands
