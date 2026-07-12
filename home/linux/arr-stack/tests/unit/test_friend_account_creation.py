import urllib.error

import pytest
from arr_users_test_doubles import (
    FRIEND_USER,
    make_context,
    stub_jellyfin,
    stub_jellyseerr,
)

import user_account_operations


def test_create_rejects_existing_username(monkeypatch):
    stub_jellyfin(monkeypatch, [FRIEND_USER])
    stub_jellyseerr(monkeypatch)
    with pytest.raises(ValueError, match="already exists"):
        user_account_operations.create_friend_account(make_context(), "Rogerio")


def test_create_applies_friend_policy_and_imports_into_jellyseerr(monkeypatch):
    created = {"Id": "new-id", "Name": "Ana", "Policy": {"IsAdministrator": True}}
    jellyfin_calls = stub_jellyfin(monkeypatch, [], created_user=created)
    jellyseerr_calls = stub_jellyseerr(monkeypatch, jellyseerr_user={"id": 9})

    result = user_account_operations.create_friend_account(make_context(), "Ana")

    applied_user_id, applied_policy = jellyfin_calls["policies"][0]
    assert applied_user_id == "new-id"
    assert applied_policy["IsAdministrator"] is False
    assert applied_policy["EnableContentDeletion"] is False
    assert jellyseerr_calls["imported"] == [["new-id"]]
    assert jellyseerr_calls["permissions"] == [(9, 160)]
    assert jellyseerr_calls["emails"] == []
    assert result["jellyseerr_user_id"] == 9
    assert result["password"] == jellyfin_calls["created"][0][1]


def test_create_auto_approves_and_sets_email_when_email_given(monkeypatch):
    created = {"Id": "new-id", "Name": "Ana", "Policy": {}}
    stub_jellyfin(monkeypatch, [], created_user=created)
    jellyseerr_calls = stub_jellyseerr(monkeypatch, jellyseerr_user={"id": 9})

    user_account_operations.create_friend_account(
        make_context(), "Ana", email="ana@example.com"
    )

    assert jellyseerr_calls["permissions"] == [(9, 160)]
    assert jellyseerr_calls["emails"] == [(9, "ana@example.com")]


def test_create_uses_explicit_password_when_given(monkeypatch):
    created = {"Id": "new-id", "Name": "Ana", "Policy": {}}
    jellyfin_calls = stub_jellyfin(monkeypatch, [], created_user=created)
    stub_jellyseerr(monkeypatch, jellyseerr_user=None)

    result = user_account_operations.create_friend_account(
        make_context(), "Ana", password="chosen-password"
    )

    assert jellyfin_calls["created"] == [("Ana", "chosen-password")]
    assert result["password"] == "chosen-password"
    assert result["jellyseerr_user_id"] is None


def test_create_generates_password_when_absent(monkeypatch):
    created = {"Id": "new-id", "Name": "Ana", "Policy": {}}
    jellyfin_calls = stub_jellyfin(monkeypatch, [], created_user=created)
    stub_jellyseerr(monkeypatch)

    user_account_operations.create_friend_account(make_context(), "Ana")

    generated_password = jellyfin_calls["created"][0][1]
    assert len(generated_password) >= 16


def test_create_rolls_back_jellyfin_user_when_policy_update_fails(monkeypatch):
    created = {"Id": "new-id", "Name": "Ana", "Policy": {}}
    jellyfin_calls = stub_jellyfin(monkeypatch, [], created_user=created)
    stub_jellyseerr(monkeypatch)

    def raise_http(base_url, api_key, user_id, policy):
        raise urllib.error.HTTPError("http://jellyfin", 400, "bad request", {}, None)

    monkeypatch.setattr(
        user_account_operations.jellyfin_api_client, "update_user_policy", raise_http
    )

    with pytest.raises(urllib.error.HTTPError):
        user_account_operations.create_friend_account(make_context(), "Ana")

    assert jellyfin_calls["deleted"] == ["new-id"]


def test_create_degrades_to_import_pending_when_jellyseerr_unreachable(monkeypatch):
    created = {"Id": "new-id", "Name": "Ana", "Policy": {}}
    jellyfin_calls = stub_jellyfin(monkeypatch, [], created_user=created)
    stub_jellyseerr(monkeypatch)

    def raise_url(base_url, api_key, jellyfin_user_ids):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(
        user_account_operations.jellyseerr_api_client,
        "import_jellyfin_users",
        raise_url,
    )

    result = user_account_operations.create_friend_account(make_context(), "Ana")

    assert result["jellyseerr_user_id"] is None
    assert result["password"] == jellyfin_calls["created"][0][1]
    assert jellyfin_calls["deleted"] == []
