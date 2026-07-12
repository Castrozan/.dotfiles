import pytest
from arr_users_test_doubles import (
    ADMIN_USER,
    FRIEND_USER,
    make_context,
    stub_jellyfin,
    stub_jellyseerr,
)

import user_account_operations


def test_set_friend_email_updates_the_jellyseerr_user(monkeypatch):
    stub_jellyfin(monkeypatch, [FRIEND_USER])
    jellyseerr_calls = stub_jellyseerr(monkeypatch, jellyseerr_user={"id": 4})

    result = user_account_operations.set_friend_email(
        make_context(), "Rogerio", "rogerio@example.com"
    )

    assert jellyseerr_calls["emails"] == [(4, "rogerio@example.com")]
    assert result == {"username": "Rogerio", "email": "rogerio@example.com"}


def test_set_friend_email_rejects_missing_jellyseerr_account(monkeypatch):
    stub_jellyfin(monkeypatch, [FRIEND_USER])
    stub_jellyseerr(monkeypatch, jellyseerr_user=None)

    with pytest.raises(ValueError, match="no Jellyseerr account"):
        user_account_operations.set_friend_email(
            make_context(), "Rogerio", "rogerio@example.com"
        )


def test_set_friend_email_refuses_administrator(monkeypatch):
    stub_jellyfin(monkeypatch, [ADMIN_USER])
    stub_jellyseerr(monkeypatch, jellyseerr_user={"id": 1})

    with pytest.raises(ValueError, match="administrator"):
        user_account_operations.set_friend_email(
            make_context(), "lucas", "lucas@example.com"
        )
