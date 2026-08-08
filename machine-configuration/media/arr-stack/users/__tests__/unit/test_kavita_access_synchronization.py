import io
import sys
import urllib.error
from pathlib import Path

import pytest
from kavita_test_doubles import make_context, stub_kavita

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import kavita_access_synchronization
import kavita_api_client


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
