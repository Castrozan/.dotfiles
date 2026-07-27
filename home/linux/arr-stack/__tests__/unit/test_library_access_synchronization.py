import sys
import urllib.error
from pathlib import Path

import pytest
from arr_users_test_doubles import (
    PUBLIC_ONLY_LIBRARIES,
    SYNC_FRIEND_USER,
    make_context,
    stub_library_synchronization,
)

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import library_access_synchronization


def test_sync_creates_only_the_declared_libraries_that_are_missing(monkeypatch):
    calls = stub_library_synchronization(
        monkeypatch, [], libraries=PUBLIC_ONLY_LIBRARIES
    )

    result = library_access_synchronization.synchronize_library_access(make_context())

    assert calls["created_libraries"] == [
        ("Movies (Private)", "/media/movies-private"),
        ("TV (Private)", "/media/tv-private"),
    ]
    assert result["created_libraries"] == ["Movies (Private)", "TV (Private)"]


def test_sync_creates_nothing_when_every_library_exists(monkeypatch):
    calls = stub_library_synchronization(monkeypatch, [])

    library_access_synchronization.synchronize_library_access(make_context())

    assert calls["created_libraries"] == []


def test_sync_reports_the_public_and_private_libraries(monkeypatch):
    stub_library_synchronization(monkeypatch, [])

    result = library_access_synchronization.synchronize_library_access(make_context())

    assert result["private_libraries"] == ["Movies (Private)", "TV (Private)"]
    assert result["public_libraries"] == ["Movies", "TV"]


def test_sync_still_reconciles_visibility_when_a_library_cannot_be_created(monkeypatch):
    calls = stub_library_synchronization(
        monkeypatch,
        [SYNC_FRIEND_USER],
        libraries=PUBLIC_ONLY_LIBRARIES,
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
    calls = stub_library_synchronization(monkeypatch, [SYNC_FRIEND_USER], ready=False)

    with pytest.raises(ValueError, match="never became reachable"):
        library_access_synchronization.synchronize_library_access(make_context())

    assert calls["policies"] == []


def test_sync_writes_no_policy_when_a_public_library_vanished(monkeypatch):
    calls = stub_library_synchronization(
        monkeypatch,
        [SYNC_FRIEND_USER],
        libraries=[{"Name": "Movies (Private)", "ItemId": "movies-private-id"}],
    )

    with pytest.raises(ValueError, match="missing from Jellyfin"):
        library_access_synchronization.synchronize_library_access(make_context())

    assert calls["policies"] == []
