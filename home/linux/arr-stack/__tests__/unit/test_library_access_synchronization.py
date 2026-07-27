import sys
import urllib.error
from pathlib import Path

import pytest
from arr_users_test_doubles import DECLARED_LIBRARIES, PUBLIC_LIBRARY_IDS, make_context

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import library_access_synchronization

ADMIN_USER = {"Id": "admin-id", "Name": "lucas", "Policy": {"IsAdministrator": True}}
FRIEND_USER = {
    "Id": "friend-id",
    "Name": "Rogerio",
    "Policy": {"IsAdministrator": False, "EnableAllFolders": True},
}
DISABLED_FRIEND_USER = {
    "Id": "disabled-id",
    "Name": "xamitos",
    "Policy": {"IsAdministrator": False, "IsDisabled": True, "EnableAllFolders": True},
}


def stub_jellyfin(
    monkeypatch, users, libraries=DECLARED_LIBRARIES, ready=True, creation_error=None
):
    calls = {"policies": [], "created_libraries": []}

    def create_virtual_folder(base_url, api_key, name, collection_type, path):
        if creation_error is not None:
            raise creation_error
        calls["created_libraries"].append((name, path))

    monkeypatch.setattr(
        library_access_synchronization.jellyfin_api_client,
        "wait_until_ready",
        lambda base_url, api_key: ready,
    )
    monkeypatch.setattr(
        library_access_synchronization.jellyfin_api_client,
        "list_virtual_folders",
        lambda base_url, api_key: libraries,
    )
    monkeypatch.setattr(
        library_access_synchronization.jellyfin_api_client,
        "list_users",
        lambda base_url, api_key: users,
    )
    monkeypatch.setattr(
        library_access_synchronization.jellyfin_api_client,
        "update_user_policy",
        lambda base_url, api_key, user_id, policy: calls["policies"].append(
            (user_id, policy)
        ),
    )
    monkeypatch.setattr(
        library_access_synchronization.jellyfin_api_client,
        "create_virtual_folder",
        create_virtual_folder,
    )
    return calls


def test_sync_restricts_every_friend_to_the_public_libraries(monkeypatch):
    calls = stub_jellyfin(monkeypatch, [ADMIN_USER, FRIEND_USER])

    result = library_access_synchronization.synchronize_library_access(make_context())

    applied_user_id, applied_policy = calls["policies"][0]
    assert applied_user_id == "friend-id"
    assert applied_policy["EnableAllFolders"] is False
    assert applied_policy["EnabledFolders"] == PUBLIC_LIBRARY_IDS
    assert result["reconciled_accounts"] == ["Rogerio"]


def test_sync_never_touches_an_administrator(monkeypatch):
    calls = stub_jellyfin(monkeypatch, [ADMIN_USER])

    result = library_access_synchronization.synchronize_library_access(make_context())

    assert calls["policies"] == []
    assert result["reconciled_accounts"] == []


def test_sync_keeps_a_disabled_friend_disabled(monkeypatch):
    calls = stub_jellyfin(monkeypatch, [DISABLED_FRIEND_USER])

    library_access_synchronization.synchronize_library_access(make_context())

    _, applied_policy = calls["policies"][0]
    assert applied_policy["IsDisabled"] is True
    assert applied_policy["EnableAllFolders"] is False


def test_sync_creates_only_the_declared_libraries_that_are_missing(monkeypatch):
    calls = stub_jellyfin(
        monkeypatch,
        [],
        libraries=[
            {"Name": "Movies", "ItemId": "movies-id"},
            {"Name": "TV", "ItemId": "tv-id"},
        ],
    )

    result = library_access_synchronization.synchronize_library_access(make_context())

    assert calls["created_libraries"] == [
        ("Movies (Private)", "/media/movies-private"),
        ("TV (Private)", "/media/tv-private"),
    ]
    assert result["created_libraries"] == ["Movies (Private)", "TV (Private)"]


def test_sync_creates_nothing_when_every_library_exists(monkeypatch):
    calls = stub_jellyfin(monkeypatch, [])

    library_access_synchronization.synchronize_library_access(make_context())

    assert calls["created_libraries"] == []


def test_sync_reports_the_private_libraries_friends_lose(monkeypatch):
    stub_jellyfin(monkeypatch, [])

    result = library_access_synchronization.synchronize_library_access(make_context())

    assert result["private_libraries"] == ["Movies (Private)", "TV (Private)"]
    assert result["public_libraries"] == ["Movies", "TV"]


def test_sync_still_reconciles_visibility_when_a_library_cannot_be_created(monkeypatch):
    calls = stub_jellyfin(
        monkeypatch,
        [FRIEND_USER],
        libraries=[
            {"Name": "Movies", "ItemId": "movies-id"},
            {"Name": "TV", "ItemId": "tv-id"},
        ],
        creation_error=urllib.error.HTTPError(
            "http://jellyfin", 400, "path does not exist", {}, None
        ),
    )

    result = library_access_synchronization.synchronize_library_access(make_context())

    _, applied_policy = calls["policies"][0]
    assert applied_policy["EnableAllFolders"] is False
    assert result["created_libraries"] == []
    assert result["failed_libraries"] == ["Movies (Private)", "TV (Private)"]


def test_sync_writes_no_policy_when_jellyfin_never_becomes_reachable(monkeypatch):
    calls = stub_jellyfin(monkeypatch, [FRIEND_USER], ready=False)

    with pytest.raises(ValueError, match="never became reachable"):
        library_access_synchronization.synchronize_library_access(make_context())

    assert calls["policies"] == []


def test_sync_writes_no_policy_when_a_public_library_vanished(monkeypatch):
    calls = stub_jellyfin(
        monkeypatch,
        [FRIEND_USER],
        libraries=[{"Name": "Movies (Private)", "ItemId": "movies-private-id"}],
    )

    with pytest.raises(ValueError, match="missing from Jellyfin"):
        library_access_synchronization.synchronize_library_access(make_context())

    assert calls["policies"] == []
