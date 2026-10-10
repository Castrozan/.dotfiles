import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from shorts_browser_pages.ownership import BrowserPages


@pytest.fixture
def browser_pages(tmp_path, monkeypatch):
    targets = {"operator-tab": {"id": "operator-tab", "url": "https://example.com"}}
    commands = []

    def execute(arguments, **options):
        command = arguments[3:]
        commands.append(command)
        if command[:2] == ["tab", "--json"]:
            return SimpleNamespace(stdout=json.dumps({"tabs": list(targets.values())}))
        if command[0] == "close":
            del targets[command[1]]
            return SimpleNamespace(stdout="{}")
        raise AssertionError(command)

    def create(server):
        identifier = f"owned-{len(targets)}"
        targets[identifier] = {"id": identifier, "url": "about:blank"}
        commands.append(["create"])
        return identifier

    monkeypatch.setattr("shorts_browser_pages.ownership.subprocess.run", execute)
    monkeypatch.setattr("shorts_browser_pages.ownership.create_page", create)
    pages = BrowserPages(
        tmp_path, "morning", ["pinchtab", "--server", "http://local"], "instance"
    )
    pages.begin()
    return pages, targets, commands


def test_repeated_new_tabs_reuse_two_owned_pages(browser_pages):
    pages, targets, commands = browser_pages
    with pages.lock():
        for index in range(22):
            hostname = "studio.youtube.com" if index % 2 else "www.youtube.com"
            arguments = pages.arguments(
                ["nav", f"https://{hostname}/{index}", "--new-tab"]
            )
            assert "--new-tab" not in arguments
            assert arguments[-2:] == [
                "--tab",
                "owned-1" if index % 2 == 0 else "owned-2",
            ]
    assert len(targets) == 3
    assert sum(command[0] == "create" for command in commands) == 2
    pages.cleanup()
    assert list(targets) == ["operator-tab"]


@pytest.mark.parametrize(
    "arguments",
    [
        ["nav", "https://studio.youtube.com", "--tab", "operator-tab"],
        ["snap", "--tab=operator-tab"],
        ["tab", "operator-tab"],
        ["close", "operator-tab"],
    ],
)
def test_operator_tabs_cannot_receive_run_actions(browser_pages, arguments):
    pages, targets, commands = browser_pages
    with pages.lock(), pytest.raises(ValueError, match="owned"):
        pages.arguments(arguments)
    assert list(targets) == ["operator-tab"]
    assert commands == []


def test_cleanup_preserves_concurrently_opened_operator_tab(browser_pages):
    pages, targets, commands = browser_pages
    with pages.lock():
        pages.arguments(["nav", "https://www.youtube.com", "--new-tab"])
    targets["new-operator-tab"] = {
        "id": "new-operator-tab",
        "url": "https://example.org",
    }
    pages.cleanup()
    pages.cleanup()
    assert set(targets) == {"operator-tab", "new-operator-tab"}
    assert [command for command in commands if command[0] == "close"] == [
        ["close", "owned-1", "--json"]
    ]


def test_finished_run_cannot_reopen_pages(browser_pages):
    pages, targets, commands = browser_pages
    pages.cleanup()
    with pages.lock(), pytest.raises(ValueError, match="finished"):
        pages.arguments(["nav", "https://studio.youtube.com", "--new-tab"])
    assert list(targets) == ["operator-tab"]


def test_next_run_reclaims_recorded_leftovers(browser_pages):
    pages, targets, commands = browser_pages
    with pages.lock():
        pages.arguments(["nav", "https://studio.youtube.com", "--new-tab"])
    afternoon = BrowserPages(pages.root, "afternoon", pages.command, "instance")
    afternoon.begin()
    assert list(targets) == ["operator-tab"]
    with pages.lock(), pytest.raises(ValueError, match="owned"):
        pages.arguments(["nav", "https://www.youtube.com", "--new-tab"])


def test_failed_cleanup_retains_ownership_and_blocks_next_run(
    browser_pages, monkeypatch
):
    pages, targets, commands = browser_pages
    with pages.lock():
        pages.arguments(["nav", "https://studio.youtube.com", "--new-tab"])
    execute = Mock(side_effect=RuntimeError("browser unavailable"))
    monkeypatch.setattr("shorts_browser_pages.ownership.subprocess.run", execute)
    with pytest.raises(RuntimeError, match="unavailable"):
        pages.cleanup()
    state = json.loads((pages.root / "browser-pages.json").read_text())
    assert state["finished"] is True
    assert state["pages"] == {"publisher": "owned-1"}
    afternoon = BrowserPages(pages.root, "afternoon", pages.command, "instance")
    with pytest.raises(RuntimeError, match="unavailable"):
        afternoon.begin()


def test_concurrent_allocations_share_one_page(browser_pages):
    pages, targets, commands = browser_pages

    def navigate(index):
        with pages.lock():
            return pages.arguments(
                ["nav", f"https://www.youtube.com/{index}", "--new-tab"]
            )[-1]

    with ThreadPoolExecutor(max_workers=8) as workers:
        identifiers = list(workers.map(navigate, range(22)))
    assert set(identifiers) == {"owned-1"}
    assert len(targets) == 2


def test_lost_creation_response_blocks_retry_without_closing_unknown_tabs(
    browser_pages, monkeypatch
):
    pages, targets, commands = browser_pages
    execute = Mock(side_effect=RuntimeError("response lost"))
    with monkeypatch.context() as patch:
        patch.setattr("shorts_browser_pages.ownership.create_page", execute)
        with pages.lock(), pytest.raises(RuntimeError, match="response lost"):
            pages.arguments(["nav", "https://studio.youtube.com", "--new-tab"])
    targets["ambiguous-owned-tab"] = {"id": "ambiguous-owned-tab", "url": "about:blank"}
    with pages.lock(), pytest.raises(ValueError, match="ambiguous"):
        pages.arguments(["nav", "https://studio.youtube.com", "--new-tab"])
    with pytest.raises(ValueError, match="ambiguous"):
        pages.cleanup()
    afternoon = BrowserPages(pages.root, "afternoon", pages.command, "instance")
    with pytest.raises(ValueError, match="ambiguous"):
        afternoon.begin()
    assert set(targets) == {"operator-tab", "ambiguous-owned-tab"}


def test_closed_page_can_be_replaced_without_increasing_bound(browser_pages):
    pages, targets, commands = browser_pages
    with pages.lock():
        arguments = pages.arguments(["nav", "https://studio.youtube.com", "--new-tab"])
    del targets[arguments[-1]]
    with pages.lock():
        pages.arguments(["nav", "https://studio.youtube.com", "--new-tab"])
    assert len(targets) == 2


def test_tab_listing_exposes_only_owned_pages(browser_pages):
    pages, targets, commands = browser_pages
    with pages.lock():
        pages.arguments(["nav", "https://studio.youtube.com", "--new-tab"])
        assert [target["id"] for target in pages.tabs()["tabs"]] == ["owned-1"]


def test_default_action_targets_last_owned_page(browser_pages):
    pages, targets, commands = browser_pages
    with pages.lock():
        pages.arguments(["nav", "https://studio.youtube.com", "--new-tab"])
        assert pages.arguments(["snap"]) == ["snap", "--tab", "owned-1"]


def test_instance_replacement_does_not_close_new_browser_tabs(browser_pages):
    pages, targets, commands = browser_pages
    with pages.lock():
        pages.arguments(["nav", "https://studio.youtube.com", "--new-tab"])
    replacement = BrowserPages(pages.root, "afternoon", pages.command, "new-instance")
    replacement.begin()
    assert not any(command[0] == "close" for command in commands)
