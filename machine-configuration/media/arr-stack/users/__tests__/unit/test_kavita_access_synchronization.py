import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import kavita_access_synchronization
import kavita_api_client
import kavita_library_source_folders
import user_account_operations

KAVITA_LIBRARIES = [
    {"id": 1, "name": "Manga", "folders": ["/manga"], "type": 0},
    {"id": 2, "name": "Manga (Private)", "folders": ["/manga-private"], "type": 0},
]
KAVITA_USERS = [
    {"id": 1, "username": "zanoni", "roles": ["Admin", "Login"]},
    {"id": 4, "username": "Xamitos", "roles": ["Login", "Download", "Pleb"]},
]


def make_context():
    return user_account_operations.ArrUsersContext(
        kavita_base_url="http://kavita", kavita_api_key="key"
    )


def stub_kavita(monkeypatch, libraries=None, users=None):
    account_updates = []
    library_updates = []
    monkeypatch.setenv("ARR_USERS_KAVITA_PUBLIC_LIBRARIES", json.dumps(["Manga"]))
    monkeypatch.setenv("ARR_USERS_KAVITA_PRIVILEGED_ACCOUNTS", json.dumps(["zanoni"]))
    monkeypatch.setenv("ARR_USERS_KAVITA_FRIEND_ACCOUNTS", json.dumps(["Xamitos"]))
    monkeypatch.setattr(
        kavita_api_client, "wait_for_bearer_token", lambda base_url, api_key: "jwt"
    )
    monkeypatch.setattr(
        kavita_api_client,
        "list_libraries",
        lambda base_url, token: KAVITA_LIBRARIES if libraries is None else libraries,
    )
    monkeypatch.setattr(
        kavita_api_client,
        "list_users",
        lambda base_url, token: KAVITA_USERS if users is None else users,
    )
    monkeypatch.setattr(
        kavita_api_client,
        "update_account",
        lambda base_url, token, account_update: account_updates.append(account_update),
    )
    monkeypatch.setattr(
        kavita_api_client,
        "update_library",
        lambda base_url, token, library_update: library_updates.append(library_update),
    )
    return account_updates, library_updates


def test_the_reconcile_withholds_the_private_library_from_a_friend(monkeypatch):
    account_updates, _ = stub_kavita(monkeypatch)

    result = kavita_access_synchronization.synchronize_kavita_library_access(
        make_context()
    )

    libraries_by_username = {
        account_update["username"]: account_update["libraries"]
        for account_update in account_updates
    }
    assert libraries_by_username == {"zanoni": [1, 2], "Xamitos": [1]}
    assert result["private_libraries"] == ["Manga (Private)"]
    assert result["reconciled_accounts"] == ["zanoni", "Xamitos"]


def test_every_account_is_rewritten_so_none_keeps_a_stale_grant(monkeypatch):
    account_updates, _ = stub_kavita(
        monkeypatch,
        users=[{"id": 7, "username": "stranger", "roles": ["Admin", "Login"]}],
    )

    result = kavita_access_synchronization.synchronize_kavita_library_access(
        make_context()
    )

    assert account_updates[0]["libraries"] == [1]
    assert account_updates[0]["roles"] == ["Login"]
    assert result["undeclared_accounts"] == ["stranger"]


def test_a_missing_declared_library_stops_the_reconcile_before_any_write(monkeypatch):
    account_updates, _ = stub_kavita(
        monkeypatch, libraries=[{"id": 2, "name": "Manga (Private)"}]
    )

    with pytest.raises(ValueError) as error_info:
        kavita_access_synchronization.synchronize_kavita_library_access(make_context())
    assert "Manga" in str(error_info.value)
    assert account_updates == []


def test_an_unreachable_kavita_leaves_the_boundary_alone(monkeypatch):
    account_updates, _ = stub_kavita(monkeypatch)
    monkeypatch.setattr(
        kavita_api_client, "wait_for_bearer_token", lambda base_url, api_key: None
    )

    with pytest.raises(ValueError) as error_info:
        kavita_access_synchronization.synchronize_kavita_library_access(make_context())
    assert "never became reachable" in str(error_info.value)
    assert account_updates == []


def test_the_manga_library_is_repointed_at_each_source_directory(monkeypatch, tmp_path):
    _, library_updates = stub_kavita(monkeypatch)
    (tmp_path / "MangaDex (EN)").mkdir()
    (tmp_path / "Weeb Central").mkdir()
    (tmp_path / "loose-file.cbz").write_text("")
    monkeypatch.setenv("ARR_USERS_KAVITA_SOURCE_FOLDER_LIBRARY", "Manga")
    monkeypatch.setenv("ARR_USERS_KAVITA_SOURCE_ROOT_HOST_PATH", str(tmp_path))
    monkeypatch.setenv("ARR_USERS_KAVITA_SOURCE_ROOT_CONTAINER_PATH", "/manga")

    result = kavita_access_synchronization.synchronize_kavita_library_access(
        make_context()
    )

    assert result["repointed_libraries"] == ["Manga"]
    assert library_updates[0]["folders"] == [
        "/manga/MangaDex (EN)",
        "/manga/Weeb Central",
    ]
    assert library_updates[0]["id"] == 1


def test_a_library_already_pointing_at_its_sources_is_left_alone(monkeypatch, tmp_path):
    _, library_updates = stub_kavita(
        monkeypatch,
        libraries=[
            {"id": 1, "name": "Manga", "folders": ["/manga/MangaDex (EN)"], "type": 0}
        ],
    )
    (tmp_path / "MangaDex (EN)").mkdir()
    monkeypatch.setenv("ARR_USERS_KAVITA_SOURCE_FOLDER_LIBRARY", "Manga")
    monkeypatch.setenv("ARR_USERS_KAVITA_SOURCE_ROOT_HOST_PATH", str(tmp_path))
    monkeypatch.setenv("ARR_USERS_KAVITA_SOURCE_ROOT_CONTAINER_PATH", "/manga")

    result = kavita_access_synchronization.synchronize_kavita_library_access(
        make_context()
    )

    assert result["repointed_libraries"] == []
    assert library_updates == []


def test_an_empty_source_root_never_blanks_the_library_folders(monkeypatch, tmp_path):
    _, library_updates = stub_kavita(monkeypatch)
    monkeypatch.setenv("ARR_USERS_KAVITA_SOURCE_FOLDER_LIBRARY", "Manga")
    monkeypatch.setenv("ARR_USERS_KAVITA_SOURCE_ROOT_HOST_PATH", str(tmp_path))
    monkeypatch.setenv("ARR_USERS_KAVITA_SOURCE_ROOT_CONTAINER_PATH", "/manga")

    assert kavita_library_source_folders.resolve_source_library_folders() == []
    kavita_access_synchronization.synchronize_kavita_library_access(make_context())
    assert library_updates == []


def test_a_rejected_api_key_fails_without_retrying(monkeypatch):
    attempts = []

    def raise_unauthorized(base_url, api_key):
        attempts.append(api_key)
        raise urllib.error.HTTPError(
            f"{base_url}/api/Plugin/authenticate", 401, "no", {}, io.BytesIO(b"")
        )

    monkeypatch.setattr(kavita_api_client, "authenticate", raise_unauthorized)

    with pytest.raises(urllib.error.HTTPError):
        kavita_api_client.wait_for_bearer_token("http://kavita", "wrong")
    assert len(attempts) == 1
