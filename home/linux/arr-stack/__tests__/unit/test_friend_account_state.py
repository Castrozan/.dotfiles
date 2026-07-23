import pytest
from arr_users_test_doubles import (
    ADMIN_USER,
    FRIEND_USER,
    make_context,
    stub_jellyfin,
    stub_jellyseerr,
)

import user_account_operations


def test_reset_password_refuses_administrator(monkeypatch):
    jellyfin_calls = stub_jellyfin(monkeypatch, [ADMIN_USER])
    stub_jellyseerr(monkeypatch)
    with pytest.raises(ValueError, match="administrator"):
        user_account_operations.reset_friend_password(make_context(), "lucas")
    assert jellyfin_calls["passwords"] == []


def test_reset_password_sets_new_password(monkeypatch):
    jellyfin_calls = stub_jellyfin(monkeypatch, [FRIEND_USER])
    stub_jellyseerr(monkeypatch)

    result = user_account_operations.reset_friend_password(make_context(), "Rogerio")

    assert jellyfin_calls["passwords"][0][0] == "friend-id"
    assert result["password"] == jellyfin_calls["passwords"][0][1]


def test_reset_password_uses_explicit_password(monkeypatch):
    jellyfin_calls = stub_jellyfin(monkeypatch, [FRIEND_USER])
    stub_jellyseerr(monkeypatch)

    result = user_account_operations.reset_friend_password(
        make_context(), "Rogerio", password="chosen"
    )

    assert jellyfin_calls["passwords"][0] == ("friend-id", "chosen")
    assert result["password"] == "chosen"


def test_disable_refuses_administrator(monkeypatch):
    jellyfin_calls = stub_jellyfin(monkeypatch, [ADMIN_USER])
    stub_jellyseerr(monkeypatch)
    with pytest.raises(ValueError, match="administrator"):
        user_account_operations.set_friend_account_enabled(
            make_context(), "lucas", False
        )
    assert jellyfin_calls["policies"] == []


def test_disable_sets_is_disabled_on_policy(monkeypatch):
    jellyfin_calls = stub_jellyfin(monkeypatch, [FRIEND_USER])
    stub_jellyseerr(monkeypatch)

    user_account_operations.set_friend_account_enabled(make_context(), "Rogerio", False)

    _, applied_policy = jellyfin_calls["policies"][0]
    assert applied_policy["IsDisabled"] is True


def test_enable_clears_is_disabled_on_policy(monkeypatch):
    jellyfin_calls = stub_jellyfin(monkeypatch, [FRIEND_USER])
    stub_jellyseerr(monkeypatch)

    user_account_operations.set_friend_account_enabled(make_context(), "Rogerio", True)

    _, applied_policy = jellyfin_calls["policies"][0]
    assert applied_policy["IsDisabled"] is False


def test_list_accounts_joins_jellyseerr_records(monkeypatch):
    monkeypatch.setattr(
        user_account_operations.jellyfin_api_client,
        "list_users",
        lambda base_url, api_key: [FRIEND_USER, ADMIN_USER],
    )
    monkeypatch.setattr(
        user_account_operations.jellyseerr_api_client,
        "list_users",
        lambda base_url, api_key: [{"id": 4, "jellyfinUserId": "friend-id"}],
    )

    accounts = user_account_operations.list_accounts(make_context())

    by_username = {account["username"]: account for account in accounts}
    assert by_username["Rogerio"]["jellyseerr_user_id"] == 4
    assert by_username["Rogerio"]["is_administrator"] is False
    assert by_username["lucas"]["jellyseerr_user_id"] is None
    assert by_username["lucas"]["is_administrator"] is True
