import json
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest
from shorts_browser_pages.ownership import BrowserPages


def test_repeated_new_tabs_reuse_two_owned_pages(browser_pages):
    pages, targets, commands = browser_pages
    with pages.lock():
        for index in range(22):
            hostname = "studio.youtube.com" if index % 2 else "www.youtube.com"
            arguments = pages.arguments(["open", f"https://{hostname}/{index}"])
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
        ["open", "https://studio.youtube.com", "--tab", "operator-tab"],
        ["state", "--tab=operator-tab"],
        ["tab", "select", "operator-tab"],
        ["tab", "close", "operator-tab"],
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
        pages.arguments(["open", "https://www.youtube.com"])
    targets["new-operator-tab"] = {
        "id": "new-operator-tab",
        "url": "https://example.org",
    }
    pages.cleanup()
    pages.cleanup()
    assert set(targets) == {"operator-tab", "new-operator-tab"}
    assert [command for command in commands if command[:2] == ["tab", "close"]] == [
        ["tab", "close", "owned-1"]
    ]


def test_finished_run_cannot_reopen_pages(browser_pages):
    pages, targets, commands = browser_pages
    pages.cleanup()
    with pages.lock(), pytest.raises(ValueError, match="finished"):
        pages.arguments(["open", "https://studio.youtube.com"])
    assert list(targets) == ["operator-tab"]


def test_next_run_reclaims_recorded_leftovers(browser_pages):
    pages, targets, commands = browser_pages
    with pages.lock():
        pages.arguments(["open", "https://studio.youtube.com"])
    afternoon = BrowserPages(
        pages.root, "afternoon", pages.command, "instance", pages.scope
    )
    afternoon.begin()
    assert list(targets) == ["operator-tab"]
    with pages.lock(), pytest.raises(ValueError, match="owned"):
        pages.arguments(["open", "https://www.youtube.com"])


def test_failed_cleanup_retains_ownership_and_blocks_next_run(
    browser_pages, monkeypatch
):
    pages, targets, commands = browser_pages
    with pages.lock():
        pages.arguments(["open", "https://studio.youtube.com"])
    execute = Mock(side_effect=RuntimeError("browser unavailable"))
    monkeypatch.setattr("shorts_browser_pages.transport.subprocess.run", execute)
    with pytest.raises(RuntimeError, match="unavailable"):
        pages.cleanup()
    state = json.loads((pages.root / "browser-pages.json").read_text())
    assert state["finished"] is True
    assert state["pages"] == {"publisher": "owned-1"}
    afternoon = BrowserPages(
        pages.root, "afternoon", pages.command, "instance", pages.scope
    )
    with pytest.raises(RuntimeError, match="unavailable"):
        afternoon.begin()


def test_concurrent_allocations_share_one_page(browser_pages):
    pages, targets, commands = browser_pages

    def navigate(index):
        with pages.lock():
            return pages.arguments(["open", f"https://www.youtube.com/{index}"])[-1]

    with ThreadPoolExecutor(max_workers=8) as workers:
        identifiers = list(workers.map(navigate, range(22)))
    assert set(identifiers) == {"owned-1"}
    assert len(targets) == 2
