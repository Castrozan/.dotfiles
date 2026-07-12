import json
import urllib.request

JELLYSEERR_REQUEST_TIMEOUT_SECONDS = 20
JELLYSEERR_USER_PAGE_SIZE = 200


def request_json(base_url, api_key, method, path, payload=None):
    encoded_payload = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=encoded_payload,
        method=method,
        headers={
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(
        request, timeout=JELLYSEERR_REQUEST_TIMEOUT_SECONDS
    ) as response:
        response_body = response.read().decode()
    return json.loads(response_body) if response_body else None


def list_users(base_url, api_key):
    result = request_json(
        base_url, api_key, "GET", f"/api/v1/user?take={JELLYSEERR_USER_PAGE_SIZE}"
    )
    return (result or {}).get("results", [])


def find_user_by_jellyfin_user_id(base_url, api_key, jellyfin_user_id):
    for user in list_users(base_url, api_key):
        if user.get("jellyfinUserId") == jellyfin_user_id:
            return user
    return None


def import_jellyfin_users(base_url, api_key, jellyfin_user_ids):
    return (
        request_json(
            base_url,
            api_key,
            "POST",
            "/api/v1/user/import-from-jellyfin",
            {"jellyfinUserIds": jellyfin_user_ids},
        )
        or []
    )


def delete_user(base_url, api_key, jellyseerr_user_id):
    request_json(base_url, api_key, "DELETE", f"/api/v1/user/{jellyseerr_user_id}")


def set_user_permissions(base_url, api_key, jellyseerr_user_id, permissions):
    return request_json(
        base_url,
        api_key,
        "PUT",
        f"/api/v1/user/{jellyseerr_user_id}",
        {"permissions": permissions},
    )


def set_user_email(base_url, api_key, jellyseerr_user_id, email):
    current_settings = (
        request_json(
            base_url,
            api_key,
            "GET",
            f"/api/v1/user/{jellyseerr_user_id}/settings/main",
        )
        or {}
    )
    return request_json(
        base_url,
        api_key,
        "POST",
        f"/api/v1/user/{jellyseerr_user_id}/settings/main",
        {**current_settings, "email": email},
    )
