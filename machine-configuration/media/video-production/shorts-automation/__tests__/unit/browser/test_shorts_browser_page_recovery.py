from unittest.mock import Mock

import pytest
from shorts_browser_pages.ownership import BrowserPages


def test_lost_creation_response_blocks_retry_without_closing_unknown_tabs(
    browser_pages, monkeypatch
):
    pages, targets, commands = browser_pages
    execute = Mock(side_effect=RuntimeError("response lost"))
    with monkeypatch.context() as patch:
        patch.setattr("shorts_browser_pages.ownership.create_page", execute)
        with pages.lock(), pytest.raises(RuntimeError, match="response lost"):
            pages.arguments(["open", "https://studio.youtube.com"])
    targets["ambiguous-owned-tab"] = {"id": "ambiguous-owned-tab", "url": "about:blank"}
    with pages.lock(), pytest.raises(ValueError, match="ambiguous"):
        pages.arguments(["open", "https://studio.youtube.com"])
    with pytest.raises(ValueError, match="ambiguous"):
        pages.cleanup()
    afternoon = BrowserPages(
        pages.root, "afternoon", pages.command, "instance", pages.scope
    )
    with pytest.raises(ValueError, match="ambiguous"):
        afternoon.begin()
    assert set(targets) == {"operator-tab", "ambiguous-owned-tab"}


def test_closed_page_can_be_replaced_without_increasing_bound(browser_pages):
    pages, targets, commands = browser_pages
    with pages.lock():
        arguments = pages.arguments(["open", "https://studio.youtube.com"])
    del targets[arguments[-1]]
    with pages.lock():
        pages.arguments(["open", "https://studio.youtube.com"])
    assert len(targets) == 2


def test_tab_listing_exposes_only_owned_pages(browser_pages):
    pages, targets, commands = browser_pages
    with pages.lock():
        pages.arguments(["open", "https://studio.youtube.com"])
        assert [target["id"] for target in pages.tabs()["tabs"]] == ["owned-1"]


def test_default_action_targets_last_owned_page(browser_pages):
    pages, targets, commands = browser_pages
    with pages.lock():
        pages.arguments(["open", "https://studio.youtube.com"])
        assert pages.arguments(["state"]) == ["state", "--tab", "owned-1"]


def test_instance_replacement_does_not_close_new_browser_tabs(browser_pages):
    pages, targets, commands = browser_pages
    with pages.lock():
        pages.arguments(["open", "https://studio.youtube.com"])
    replacement = BrowserPages(
        pages.root, "afternoon", pages.command, "new-instance", pages.scope
    )
    replacement.begin()
    assert not any(command[:2] == ["tab", "close"] for command in commands)
