import json
import sys
import urllib.error
from pathlib import Path

import pytest

PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "suwayomi_extension_repositories"
)
sys.path.insert(0, str(PACKAGE_DIRECTORY_PATH))

import extension_repository_synchronization
import suwayomi_graphql_client

DECLARED_URLS = [
    "https://raw.githubusercontent.com/declared-one/extensions/repository-index.json",
    "https://raw.githubusercontent.com/declared-two/extensions/repository-index.json",
]


def declare(monkeypatch, tmp_path, repository_urls=None):
    list_file_path = tmp_path / "suwayomi-extension-repositories"
    list_file_path.write_text(
        json.dumps(DECLARED_URLS if repository_urls is None else repository_urls)
    )
    monkeypatch.setenv("SUWAYOMI_GRAPHQL_URL", "http://suwayomi/api/graphql")
    monkeypatch.setenv(
        "SUWAYOMI_EXTENSION_REPOSITORIES_FILE", str(list_file_path)
    )
    monkeypatch.setattr(
        suwayomi_graphql_client, "wait_until_ready", lambda graphql_url: True
    )


def test_the_declared_repositories_replace_whatever_is_stored(monkeypatch, tmp_path):
    written = []
    declare(monkeypatch, tmp_path)
    monkeypatch.setattr(
        suwayomi_graphql_client,
        "read_extension_repository_urls",
        lambda graphql_url: ["https://raw.githubusercontent.com/died/index.json"],
    )
    monkeypatch.setattr(
        suwayomi_graphql_client,
        "write_extension_repository_urls",
        lambda graphql_url, repository_urls: written.append(repository_urls)
        or list(repository_urls),
    )
    monkeypatch.setattr(
        suwayomi_graphql_client, "count_extensions_offered", lambda graphql_url: 22
    )

    result = extension_repository_synchronization.synchronize_extension_repositories()

    assert written == [DECLARED_URLS]
    assert result["rewritten"] is True
    assert result["extensions_offered"] == 22


def test_an_already_declared_list_is_not_rewritten(monkeypatch, tmp_path):
    declare(monkeypatch, tmp_path)
    monkeypatch.setattr(
        suwayomi_graphql_client,
        "read_extension_repository_urls",
        lambda graphql_url: list(DECLARED_URLS),
    )

    def refuse_write(graphql_url, repository_urls):
        raise AssertionError("an unchanged list must not be written again")

    monkeypatch.setattr(
        suwayomi_graphql_client, "write_extension_repository_urls", refuse_write
    )

    result = extension_repository_synchronization.synchronize_extension_repositories()

    assert result["rewritten"] is False
    assert result["repositories"] == DECLARED_URLS


def test_an_unreachable_suwayomi_leaves_the_repositories_alone(monkeypatch, tmp_path):
    declare(monkeypatch, tmp_path)
    monkeypatch.setattr(
        suwayomi_graphql_client, "wait_until_ready", lambda graphql_url: False
    )

    with pytest.raises(ValueError) as error_info:
        extension_repository_synchronization.synchronize_extension_repositories()
    assert "never became reachable" in str(error_info.value)


def test_a_write_that_does_not_stick_is_reported(monkeypatch, tmp_path):
    declare(monkeypatch, tmp_path)
    monkeypatch.setattr(
        suwayomi_graphql_client, "read_extension_repository_urls", lambda url: []
    )
    monkeypatch.setattr(
        suwayomi_graphql_client,
        "write_extension_repository_urls",
        lambda graphql_url, repository_urls: [],
    )

    with pytest.raises(ValueError) as error_info:
        extension_repository_synchronization.synchronize_extension_repositories()
    assert "not the declared" in str(error_info.value)


def test_an_empty_declaration_refuses_to_run(monkeypatch, tmp_path):
    declare(monkeypatch, tmp_path, repository_urls=[])

    with pytest.raises(SystemExit):
        extension_repository_synchronization.synchronize_extension_repositories()


def test_a_failed_index_never_fails_the_stored_declaration(monkeypatch, tmp_path):
    declare(monkeypatch, tmp_path)
    monkeypatch.setattr(
        suwayomi_graphql_client, "read_extension_repository_urls", lambda url: []
    )
    monkeypatch.setattr(
        suwayomi_graphql_client,
        "write_extension_repository_urls",
        lambda graphql_url, repository_urls: list(repository_urls),
    )

    def refuse_index(graphql_url, query, variables=None, timeout_seconds=None):
        raise urllib.error.URLError("connection reset")

    monkeypatch.setattr(suwayomi_graphql_client, "execute", refuse_index)

    result = extension_repository_synchronization.synchronize_extension_repositories()

    assert result["rewritten"] is True
    assert result["extensions_offered"] is None


def test_a_graphql_error_is_reported_without_its_java_stack_trace():
    assert (
        suwayomi_graphql_client.first_line_of(
            "has type STRING rather than LIST\n\tat com.typesafe.config.impl.X"
        )
        == "has type STRING rather than LIST"
    )


def test_a_host_without_the_declared_list_leaves_suwayomi_alone(monkeypatch, tmp_path):
    monkeypatch.setenv("SUWAYOMI_GRAPHQL_URL", "http://suwayomi/api/graphql")
    monkeypatch.setenv(
        "SUWAYOMI_EXTENSION_REPOSITORIES_FILE", str(tmp_path / "never-decrypted")
    )

    def refuse_contact(graphql_url):
        raise AssertionError("an undeclared host must not contact Suwayomi at all")

    monkeypatch.setattr(suwayomi_graphql_client, "wait_until_ready", refuse_contact)

    result = extension_repository_synchronization.synchronize_extension_repositories()

    assert result["repositories"] is None
    assert result["rewritten"] is False


def test_a_repository_suwayomi_would_refuse_stops_the_run(monkeypatch, tmp_path):
    declare(
        monkeypatch,
        tmp_path,
        repository_urls=[*DECLARED_URLS, "https://elsewhere.example/index.json"],
    )

    def refuse_contact(graphql_url):
        raise AssertionError("a list Suwayomi would reject must never be sent")

    monkeypatch.setattr(suwayomi_graphql_client, "wait_until_ready", refuse_contact)

    with pytest.raises(SystemExit):
        extension_repository_synchronization.synchronize_extension_repositories()
