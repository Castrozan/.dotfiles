import sys
from pathlib import Path

from arr_users_test_doubles import (
    DECLARED_LIBRARIES,
    PUBLIC_LIBRARY_IDS,
    SYNC_ADMIN_USER,
    SYNC_DISABLED_FRIEND_USER,
    SYNC_FRIEND_USER,
    SYNC_JELLYSEERR_ADMINISTRATOR_USER,
    SYNC_PRIVATE_REQUEST_USER,
    make_context,
    stub_library_synchronization,
)

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import library_access_synchronization

EVERY_LIBRARY_ID = [library["ItemId"] for library in DECLARED_LIBRARIES]


def test_a_friend_is_pinned_to_the_public_libraries(monkeypatch):
    calls = stub_library_synchronization(monkeypatch, [SYNC_FRIEND_USER])

    result = library_access_synchronization.synchronize_library_access(make_context())

    applied_user_id, applied_policy = calls["policies"][0]
    assert applied_user_id == "friend-id"
    assert applied_policy["EnableAllFolders"] is False
    assert applied_policy["EnabledFolders"] == PUBLIC_LIBRARY_IDS
    assert result["reconciled_accounts"] == ["Friend"]


def test_an_administrator_is_pinned_to_the_public_libraries_too(monkeypatch):
    calls = stub_library_synchronization(monkeypatch, [SYNC_ADMIN_USER])

    result = library_access_synchronization.synchronize_library_access(make_context())

    applied_user_id, applied_policy = calls["policies"][0]
    assert applied_user_id == "admin-id"
    assert applied_policy["EnableAllFolders"] is False
    assert applied_policy["EnabledFolders"] == PUBLIC_LIBRARY_IDS
    assert result["reconciled_accounts"] == ["owner"]


def test_pinning_an_administrator_never_demotes_it(monkeypatch):
    calls = stub_library_synchronization(monkeypatch, [SYNC_ADMIN_USER])

    library_access_synchronization.synchronize_library_access(make_context())

    _, applied_policy = calls["policies"][0]
    assert applied_policy["IsAdministrator"] is True


def test_only_the_declared_private_account_sees_every_library(monkeypatch):
    calls = stub_library_synchronization(monkeypatch, [SYNC_PRIVATE_REQUEST_USER])

    library_access_synchronization.synchronize_library_access(make_context())

    _, applied_policy = calls["policies"][0]
    assert applied_policy["EnableAllFolders"] is False
    assert applied_policy["EnabledFolders"] == EVERY_LIBRARY_ID


def test_the_jellyseerr_administrator_sees_every_library(monkeypatch):
    calls = stub_library_synchronization(
        monkeypatch, [SYNC_JELLYSEERR_ADMINISTRATOR_USER]
    )

    library_access_synchronization.synchronize_library_access(make_context())

    _, applied_policy = calls["policies"][0]
    assert applied_policy["EnableAllFolders"] is False
    assert applied_policy["EnabledFolders"] == EVERY_LIBRARY_ID


def test_the_everyday_administrator_never_gains_private_libraries(monkeypatch):
    calls = stub_library_synchronization(
        monkeypatch, [SYNC_ADMIN_USER, SYNC_JELLYSEERR_ADMINISTRATOR_USER]
    )

    library_access_synchronization.synchronize_library_access(make_context())

    everyday_policy = dict(calls["policies"])["admin-id"]
    assert everyday_policy["EnabledFolders"] == PUBLIC_LIBRARY_IDS


def test_a_disabled_friend_stays_disabled(monkeypatch):
    calls = stub_library_synchronization(monkeypatch, [SYNC_DISABLED_FRIEND_USER])

    library_access_synchronization.synchronize_library_access(make_context())

    _, applied_policy = calls["policies"][0]
    assert applied_policy["IsDisabled"] is True
    assert applied_policy["EnableAllFolders"] is False


def test_the_accounts_holding_private_access_are_reported(monkeypatch):
    stub_library_synchronization(monkeypatch, [])

    result = library_access_synchronization.synchronize_library_access(make_context())

    assert result["private_library_accounts"] == ["private-requests", "jellyseerr"]
