import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import shorts_browser
from shorts_browser import execute_browser
from shorts_store import write_document


@pytest.fixture
def scoped_browser(tmp_path, monkeypatch):
    directory = tmp_path / "runs" / "morning"
    directory.mkdir(parents=True)
    configuration = {"browser_profile": "shorts"}
    write_document(tmp_path / "config.json", configuration)
    monkeypatch.setenv("SHORTS_CONFIGURATION", str(tmp_path / "config.json"))
    monkeypatch.setenv("SHORTS_BROWSER_RUN", str(directory))
    monkeypatch.setenv("SHORTS_OPENCLI", "/bin/opencli")
    instance = Mock(return_value={"id": "instance", "scope": "/owned/profile"})
    monkeypatch.setattr(shorts_browser, "browser_instance", instance)
    pages = shorts_browser.browser_pages(directory, configuration)
    pages.begin()
    instance.reset_mock()
    monkeypatch.setattr(
        "shorts_browser_pages.ownership.create_page", lambda command, scope: "owned-tab"
    )
    targets = {"ok": True, "data": [{"page": "owned-tab"}, {"page": "operator-tab"}]}
    monkeypatch.setattr(
        "shorts_browser_pages.transport.subprocess.run",
        Mock(return_value=SimpleNamespace(stdout=json.dumps(targets), returncode=0)),
    )
    execute = Mock(return_value=0)
    monkeypatch.setattr(shorts_browser, "execute_browser", execute)
    return pages, instance, execute


def test_scoped_dispatch_supplies_job_credentials(
    scoped_browser, monkeypatch, private_browser_job_token
):
    monkeypatch.setattr(shorts_browser, "execute_browser", execute_browser)
    monkeypatch.setattr(
        shorts_browser.sys,
        "argv",
        ["shorts-browser", "open", "https://studio.youtube.com"],
    )
    assert shorts_browser.main() == 0
    environment = shorts_browser.subprocess.run.call_args.kwargs["env"]
    assert environment["OPENCLI_JOB_SCOPE"] == "/owned/profile"
    assert environment["OPENCLI_BRIDGE_TOKEN"] == private_browser_job_token


def test_wrapper_allocates_owned_page_and_checks_profile_once(
    scoped_browser, monkeypatch
):
    pages, instance, execute = scoped_browser
    monkeypatch.setattr(
        shorts_browser.sys,
        "argv",
        ["shorts-browser", "open", "https://studio.youtube.com"],
    )
    assert shorts_browser.main() == 0
    instance.assert_called_once()
    assert execute.call_args.args[0] == [
        "open",
        "https://studio.youtube.com",
        "--tab",
        "owned-tab",
    ]


@pytest.mark.parametrize(
    "arguments", [["tab", "select", "owned-tab"], ["tab", "close", "owned-tab"]]
)
def test_native_positional_tab_commands_keep_their_syntax(
    scoped_browser, monkeypatch, arguments
):
    pages, instance, execute = scoped_browser
    with pages.lock():
        pages.arguments(["open", "https://studio.youtube.com"])
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
        pages.arguments(["open", "https://studio.youtube.com"])
    monkeypatch.setattr(shorts_browser.sys, "argv", ["shorts-browser", "tab", "list"])
    assert shorts_browser.main() == 0
    assert [target["id"] for target in json.loads(capsys.readouterr().out)["tabs"]] == [
        "owned-tab"
    ]
    execute.assert_not_called()


@pytest.mark.parametrize("value", ["--help", "-h", "--tab"])
def test_literal_data_does_not_change_scope(scoped_browser, monkeypatch, value):
    pages, instance, execute = scoped_browser
    with pages.lock():
        pages.arguments(["open", "https://studio.youtube.com"])
    monkeypatch.setattr(
        shorts_browser.sys, "argv", ["shorts-browser", "type", "#field", "--", value]
    )
    assert shorts_browser.main() == 0
    assert execute.call_args.args[0] == [
        "type",
        "#field",
        "--tab",
        "owned-tab",
        "--",
        value,
    ]


def test_focusing_owned_tab_changes_default_target(scoped_browser, monkeypatch):
    pages, instance, execute = scoped_browser
    monkeypatch.setattr(
        "shorts_browser_pages.ownership.create_page",
        Mock(side_effect=["publisher-tab", "research-tab"]),
    )
    with pages.lock():
        pages.arguments(["open", "https://studio.youtube.com"])
        pages.arguments(["open", "https://www.youtube.com"])
    monkeypatch.setattr(
        shorts_browser.sys, "argv", ["shorts-browser", "tab", "select", "publisher-tab"]
    )
    assert shorts_browser.main() == 0
    monkeypatch.setattr(shorts_browser.sys, "argv", ["shorts-browser", "state"])
    assert shorts_browser.main() == 0
    assert execute.call_args.args[0] == ["state", "--tab", "publisher-tab"]
