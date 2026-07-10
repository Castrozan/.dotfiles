import pytest
from arr_users_test_doubles import (
    ADMIN_USER,
    FRIEND_USER,
    make_context,
    stub_jellyfin,
    stub_jellyseerr,
)

import user_account_operations


def test_delete_refuses_administrator(monkeypatch):
    jellyfin_calls = stub_jellyfin(monkeypatch, [ADMIN_USER])
    stub_jellyseerr(monkeypatch)
    with pytest.raises(ValueError, match="administrator"):
        user_account_operations.delete_friend_account(make_context(), "lucas")
    assert jellyfin_calls["deleted"] == []


def test_delete_removes_jellyseerr_record_and_jellyfin_user(monkeypatch):
    jellyfin_calls = stub_jellyfin(monkeypatch, [FRIEND_USER])
    jellyseerr_calls = stub_jellyseerr(monkeypatch, jellyseerr_user={"id": 4})

    user_account_operations.delete_friend_account(make_context(), "Rogerio")

    assert jellyseerr_calls["deleted"] == [4]
    assert jellyfin_calls["deleted"] == ["friend-id"]


def test_delete_tolerates_absent_jellyseerr_record(monkeypatch):
    jellyfin_calls = stub_jellyfin(monkeypatch, [FRIEND_USER])
    jellyseerr_calls = stub_jellyseerr(monkeypatch, jellyseerr_user=None)

    user_account_operations.delete_friend_account(make_context(), "Rogerio")

    assert jellyseerr_calls["deleted"] == []
    assert jellyfin_calls["deleted"] == ["friend-id"]


def test_delete_reports_unknown_username(monkeypatch):
    stub_jellyfin(monkeypatch, [])
    stub_jellyseerr(monkeypatch)
    with pytest.raises(ValueError, match="no Jellyfin user"):
        user_account_operations.delete_friend_account(make_context(), "ghost")
