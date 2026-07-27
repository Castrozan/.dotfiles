import sys
from pathlib import Path

import pytest
from arr_users_test_doubles import make_context

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import account_permission_synchronization
import jellyseerr_account_permissions

OWNER_ACCOUNT = {"id": 1, "jellyfinUsername": "jellyseerr", "permissions": 2}
DAILY_DRIVER_ACCOUNT = {"id": 2, "jellyfinUsername": "owner", "permissions": 2}
FRIEND_ACCOUNT = {"id": 4, "jellyfinUsername": "Friend", "permissions": 160}


def stub_jellyseerr(monkeypatch, users):
    calls = {"permissions": []}
    monkeypatch.setattr(
        account_permission_synchronization.jellyseerr_api_client,
        "list_users",
        lambda base_url, api_key: list(users),
    )
    monkeypatch.setattr(
        account_permission_synchronization.jellyseerr_api_client,
        "set_accounts_permissions",
        lambda base_url, api_key, user_ids, permissions: calls["permissions"].append(
            (list(user_ids), permissions)
        ),
    )
    return calls


def test_an_undeclared_administrator_is_demoted_to_requesting(monkeypatch):
    calls = stub_jellyseerr(
        monkeypatch, [OWNER_ACCOUNT, DAILY_DRIVER_ACCOUNT, FRIEND_ACCOUNT]
    )

    synchronized = account_permission_synchronization.synchronize_account_permissions(
        make_context()
    )

    assert calls["permissions"] == [
        ([2], jellyseerr_account_permissions.SELF_APPROVING_REQUESTER_PERMISSIONS)
    ]
    assert synchronized["rewritten_accounts"] == ["owner"]


def test_the_administrator_account_is_never_written_to(monkeypatch):
    calls = stub_jellyseerr(monkeypatch, [OWNER_ACCOUNT, DAILY_DRIVER_ACCOUNT])

    account_permission_synchronization.synchronize_account_permissions(make_context())

    assert 1 not in calls["permissions"][0][0]


def test_an_already_reconciled_jellyseerr_is_never_written_to(monkeypatch):
    calls = stub_jellyseerr(monkeypatch, [OWNER_ACCOUNT, FRIEND_ACCOUNT])

    synchronized = account_permission_synchronization.synchronize_account_permissions(
        make_context()
    )

    assert calls["permissions"] == []
    assert synchronized["rewritten_accounts"] == []


def test_every_non_administrator_is_reported_as_requesting_without_approval(
    monkeypatch,
):
    stub_jellyseerr(monkeypatch, [OWNER_ACCOUNT, DAILY_DRIVER_ACCOUNT, FRIEND_ACCOUNT])

    synchronized = account_permission_synchronization.synchronize_account_permissions(
        make_context()
    )

    assert synchronized["administrator_accounts"] == ["jellyseerr"]
    assert synchronized["self_approving_accounts"] == ["owner", "Friend"]


def test_nothing_is_demoted_when_no_administrator_would_be_left(monkeypatch):
    calls = stub_jellyseerr(monkeypatch, [DAILY_DRIVER_ACCOUNT, FRIEND_ACCOUNT])

    with pytest.raises(ValueError, match="administrator"):
        account_permission_synchronization.synchronize_account_permissions(
            make_context()
        )

    assert calls["permissions"] == []
