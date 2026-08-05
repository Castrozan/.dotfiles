import json
import time
import urllib.error
import urllib.parse
import urllib.request

JELLYFIN_REQUEST_TIMEOUT_SECONDS = 20
JELLYFIN_READINESS_ATTEMPTS = 30
JELLYFIN_READINESS_DELAY_SECONDS = 4


def request_json(base_url, api_key, method, path, payload=None):
    encoded_payload = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=encoded_payload,
        method=method,
        headers={
            "X-Emby-Token": api_key,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(
        request, timeout=JELLYFIN_REQUEST_TIMEOUT_SECONDS
    ) as response:
        response_body = response.read().decode()
    return json.loads(response_body) if response_body else None


def wait_until_ready(base_url, api_key):
    for remaining_attempt in range(JELLYFIN_READINESS_ATTEMPTS, 0, -1):
        try:
            request_json(base_url, api_key, "GET", "/System/Info")
            return True
        except (urllib.error.URLError, OSError):
            if remaining_attempt == 1:
                return False
            time.sleep(JELLYFIN_READINESS_DELAY_SECONDS)
    return False


def list_users(base_url, api_key):
    return request_json(base_url, api_key, "GET", "/Users") or []


def find_user_by_name(base_url, api_key, username):
    normalized_username = username.lower()
    for user in list_users(base_url, api_key):
        if user.get("Name", "").lower() == normalized_username:
            return user
    return None


def get_user(base_url, api_key, jellyfin_user_id):
    return request_json(base_url, api_key, "GET", f"/Users/{jellyfin_user_id}")


def create_user(base_url, api_key, username, password):
    return request_json(
        base_url,
        api_key,
        "POST",
        "/Users/New",
        {"Name": username, "Password": password},
    )


def delete_user(base_url, api_key, jellyfin_user_id):
    request_json(base_url, api_key, "DELETE", f"/Users/{jellyfin_user_id}")


def update_user_policy(base_url, api_key, jellyfin_user_id, policy):
    request_json(base_url, api_key, "POST", f"/Users/{jellyfin_user_id}/Policy", policy)


def set_user_password(base_url, api_key, jellyfin_user_id, new_password):
    request_json(
        base_url,
        api_key,
        "POST",
        f"/Users/Password?userId={jellyfin_user_id}",
        {"CurrentPw": "", "NewPw": new_password, "ResetPassword": False},
    )


def list_virtual_folders(base_url, api_key):
    return request_json(base_url, api_key, "GET", "/Library/VirtualFolders") or []


def create_virtual_folder(base_url, api_key, name, collection_type, container_path):
    query_string = urllib.parse.urlencode(
        {
            "name": name,
            "collectionType": collection_type,
            "refreshLibrary": "true",
        }
    )
    request_json(
        base_url,
        api_key,
        "POST",
        f"/Library/VirtualFolders?{query_string}",
        {"LibraryOptions": {"PathInfos": [{"Path": container_path}]}},
    )
