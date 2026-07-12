import sys
from pathlib import Path

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import jellyfin_api_client
import jellyseerr_api_client


def test_jellyseerr_list_users_falls_back_to_empty_on_none(monkeypatch):
    monkeypatch.setattr(
        jellyseerr_api_client, "request_json", lambda *args, **kwargs: None
    )
    assert jellyseerr_api_client.list_users("base", "key") == []


def test_jellyseerr_find_user_by_jellyfin_user_id_matches(monkeypatch):
    monkeypatch.setattr(
        jellyseerr_api_client,
        "request_json",
        lambda *args, **kwargs: {"results": [{"id": 5, "jellyfinUserId": "x"}]},
    )
    assert (
        jellyseerr_api_client.find_user_by_jellyfin_user_id("base", "key", "x")["id"]
        == 5
    )
    assert (
        jellyseerr_api_client.find_user_by_jellyfin_user_id("base", "key", "y") is None
    )


def test_jellyseerr_import_falls_back_to_empty_on_none(monkeypatch):
    monkeypatch.setattr(
        jellyseerr_api_client, "request_json", lambda *args, **kwargs: None
    )
    assert jellyseerr_api_client.import_jellyfin_users("base", "key", ["a"]) == []


def test_jellyseerr_set_user_permissions_sends_put_with_permissions(monkeypatch):
    captured = {}

    def capture_request(base_url, api_key, method, path, payload=None):
        captured.update(method=method, path=path, payload=payload)

    monkeypatch.setattr(jellyseerr_api_client, "request_json", capture_request)
    jellyseerr_api_client.set_user_permissions("base", "key", 7, 160)

    assert captured["method"] == "PUT"
    assert captured["path"] == "/api/v1/user/7"
    assert captured["payload"] == {"permissions": 160}


def test_jellyseerr_set_user_email_round_trips_current_settings(monkeypatch):
    calls = []

    def fake_request(base_url, api_key, method, path, payload=None):
        calls.append({"method": method, "path": path, "payload": payload})
        if method == "GET":
            return {"username": None, "locale": "pt-BR"}
        return {"email": payload["email"]}

    monkeypatch.setattr(jellyseerr_api_client, "request_json", fake_request)
    jellyseerr_api_client.set_user_email("base", "key", 4, "friend@example.com")

    get_call, post_call = calls
    assert get_call["method"] == "GET"
    assert get_call["path"] == "/api/v1/user/4/settings/main"
    assert post_call["method"] == "POST"
    assert post_call["path"] == "/api/v1/user/4/settings/main"
    assert post_call["payload"] == {
        "username": None,
        "locale": "pt-BR",
        "email": "friend@example.com",
    }


def test_jellyseerr_set_user_email_tolerates_missing_settings(monkeypatch):
    calls = []

    def fake_request(base_url, api_key, method, path, payload=None):
        calls.append(payload)
        return None

    monkeypatch.setattr(jellyseerr_api_client, "request_json", fake_request)
    jellyseerr_api_client.set_user_email("base", "key", 4, "friend@example.com")

    assert calls[1] == {"email": "friend@example.com"}


def test_jellyfin_list_users_falls_back_to_empty_on_none(monkeypatch):
    monkeypatch.setattr(
        jellyfin_api_client, "request_json", lambda *args, **kwargs: None
    )
    assert jellyfin_api_client.list_users("base", "key") == []


def test_jellyfin_find_user_by_name_is_case_insensitive_and_tolerates_missing_name(
    monkeypatch,
):
    users = [{"Name": "Rogerio", "Id": "1"}, {"Id": "2"}]
    monkeypatch.setattr(jellyfin_api_client, "request_json", lambda *a, **k: users)
    assert jellyfin_api_client.find_user_by_name("base", "key", "rogerio")["Id"] == "1"
    assert jellyfin_api_client.find_user_by_name("base", "key", "ghost") is None


def test_jellyfin_set_user_password_sends_expected_method_path_and_payload(monkeypatch):
    captured = {}

    def capture_request(base_url, api_key, method, path, payload=None):
        captured.update(method=method, path=path, payload=payload)

    monkeypatch.setattr(jellyfin_api_client, "request_json", capture_request)
    jellyfin_api_client.set_user_password("base", "key", "user-id", "new-pw")

    assert captured["method"] == "POST"
    assert captured["path"] == "/Users/Password?userId=user-id"
    assert captured["payload"] == {
        "CurrentPw": "",
        "NewPw": "new-pw",
        "ResetPassword": False,
    }


def test_jellyfin_create_user_sends_name_and_password(monkeypatch):
    captured = {}

    def capture_request(base_url, api_key, method, path, payload=None):
        captured.update(method=method, path=path, payload=payload)
        return {"Id": "new-id"}

    monkeypatch.setattr(jellyfin_api_client, "request_json", capture_request)
    result = jellyfin_api_client.create_user("base", "key", "Ana", "pw")

    assert captured["method"] == "POST"
    assert captured["path"] == "/Users/New"
    assert captured["payload"] == {"Name": "Ana", "Password": "pw"}
    assert result["Id"] == "new-id"
