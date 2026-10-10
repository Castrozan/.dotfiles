import io
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import shorts_browser
from shorts_browser_pages.transport import create_page
from shorts_store import write_document


@pytest.fixture
def scoped_browser(tmp_path, monkeypatch):
    directory = tmp_path / "runs" / "morning"
    directory.mkdir(parents=True)
    configuration = {
        "browser_profile_id": "authorized-profile",
        "browser_profile": "shorts",
    }
    write_document(tmp_path / "config.json", configuration)
    monkeypatch.setenv("SHORTS_CONFIGURATION", str(tmp_path / "config.json"))
    monkeypatch.setenv("SHORTS_BROWSER_RUN", str(directory))
    monkeypatch.setenv("SHORTS_PINCHTAB", "/bin/pinchtab")
    instance = Mock(return_value={"id": "instance", "url": "http://127.0.0.1:9868"})
    monkeypatch.setattr(shorts_browser, "browser_instance", instance)
    pages = shorts_browser.browser_pages(directory, configuration)
    pages.begin()
    instance.reset_mock()
    monkeypatch.setattr(
        "shorts_browser_pages.ownership.create_page", lambda server: "owned-tab"
    )
    targets = {"tabs": [{"id": "owned-tab"}, {"id": "operator-tab"}]}
    monkeypatch.setattr(
        "shorts_browser_pages.ownership.subprocess.run",
        Mock(return_value=SimpleNamespace(stdout=json.dumps(targets))),
    )
    execute = Mock(return_value=0)
    monkeypatch.setattr(shorts_browser, "execute_browser", execute)
    return pages, instance, execute


def test_wrapper_allocates_owned_page_and_checks_profile_once(
    scoped_browser, monkeypatch
):
    pages, instance, execute = scoped_browser
    monkeypatch.setattr(
        shorts_browser.sys,
        "argv",
        ["shorts-browser", "nav", "https://studio.youtube.com", "--new-tab"],
    )
    assert shorts_browser.main() == 0
    instance.assert_called_once()
    assert execute.call_args.args[0] == [
        "nav",
        "https://studio.youtube.com",
        "--tab",
        "owned-tab",
    ]


@pytest.mark.parametrize(
    "arguments",
    [
        ["tab", "close", "owned-tab"],
        ["handoff", "owned-tab"],
        ["handoff-status", "owned-tab"],
        ["resume", "owned-tab"],
    ],
)
def test_native_positional_tab_commands_keep_their_syntax(
    scoped_browser, monkeypatch, arguments
):
    pages, instance, execute = scoped_browser
    with pages.lock():
        pages.arguments(["nav", "https://studio.youtube.com"])
    monkeypatch.setattr(shorts_browser.sys, "argv", ["shorts-browser", *arguments])
    assert shorts_browser.main() == 0
    assert execute.call_args.args[0] == arguments


def test_wrapper_rejects_operator_tab_before_dispatch(scoped_browser, monkeypatch):
    pages, instance, execute = scoped_browser
    monkeypatch.setattr(
        shorts_browser.sys, "argv", ["shorts-browser", "tab", "close", "operator-tab"]
    )
    with pytest.raises(ValueError, match="owned"):
        shorts_browser.main()
    execute.assert_not_called()


def test_wrapper_lists_only_owned_tabs(scoped_browser, monkeypatch, capsys):
    pages, instance, execute = scoped_browser
    with pages.lock():
        pages.arguments(["nav", "https://studio.youtube.com"])
    monkeypatch.setattr(shorts_browser.sys, "argv", ["shorts-browser", "tab"])
    assert shorts_browser.main() == 0
    assert json.loads(capsys.readouterr().out) == {"tabs": [{"id": "owned-tab"}]}
    execute.assert_not_called()


def test_native_blank_page_creation_is_authenticated_and_returns_target(monkeypatch):
    monkeypatch.setattr(
        "shorts_browser_pages.transport.read_document",
        lambda path: {"server": {"token": "fixture-credential"}},
    )
    response = io.BytesIO(b'{"tabId":"owned-tab"}')
    send = Mock(return_value=response)
    monkeypatch.setattr("shorts_browser_pages.transport.urlopen", send)
    assert create_page("http://127.0.0.1:9868") == "owned-tab"
    request = send.call_args.args[0]
    assert request.full_url == "http://127.0.0.1:9868/tab"
    assert request.get_method() == "POST"
    assert json.loads(request.data) == {"action": "new"}
    assert request.get_header("Authorization") == "Bearer fixture-credential"


@pytest.mark.parametrize(
    "arguments, expected",
    [
        (["type", "--", "--tab"], ["type", "--tab", "owned-tab", "--", "--tab"]),
        (
            ["handoff", "--reason", "captcha", "owned-tab"],
            ["handoff", "owned-tab", "--reason", "captcha"],
        ),
        (
            ["handoff", "--reason", "--tab", "owned-tab"],
            ["handoff", "owned-tab", "--reason", "--tab"],
        ),
        (
            ["tab", "close", "--json", "owned-tab"],
            ["tab", "close", "owned-tab", "--json"],
        ),
    ],
)
def test_native_flag_order_and_literal_data_are_preserved(
    scoped_browser, monkeypatch, arguments, expected
):
    pages, instance, execute = scoped_browser
    with pages.lock():
        pages.arguments(["nav", "https://studio.youtube.com"])
    monkeypatch.setattr(shorts_browser.sys, "argv", ["shorts-browser", *arguments])
    assert shorts_browser.main() == 0
    assert execute.call_args.args[0] == expected


def test_focusing_an_owned_tab_changes_the_default_target(scoped_browser, monkeypatch):
    pages, instance, execute = scoped_browser
    monkeypatch.setattr(
        "shorts_browser_pages.ownership.create_page",
        Mock(side_effect=["publisher-tab", "research-tab"]),
    )
    with pages.lock():
        pages.arguments(["nav", "https://studio.youtube.com"])
        pages.arguments(["nav", "https://www.youtube.com"])
    monkeypatch.setattr(
        shorts_browser.sys, "argv", ["shorts-browser", "tab", "publisher-tab"]
    )
    assert shorts_browser.main() == 0
    monkeypatch.setattr(shorts_browser.sys, "argv", ["shorts-browser", "snap"])
    assert shorts_browser.main() == 0
    assert execute.call_args.args[0] == ["snap", "--tab", "publisher-tab"]
