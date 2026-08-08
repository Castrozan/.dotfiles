import json
import sys
from pathlib import Path

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import kavita_api_client
import user_account_operations

KAVITA_LIBRARIES = [
    {
        "id": 1,
        "name": "Manga",
        "folders": ["/manga"],
        "type": 0,
        "libraryFileTypes": [1],
    },
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


def declare_source_root(monkeypatch, host_root_path):
    monkeypatch.setenv("ARR_USERS_KAVITA_SOURCE_FOLDER_LIBRARY", "Manga")
    monkeypatch.setenv("ARR_USERS_KAVITA_SOURCE_ROOT_HOST_PATH", str(host_root_path))
    monkeypatch.setenv("ARR_USERS_KAVITA_SOURCE_ROOT_CONTAINER_PATH", "/manga")


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
