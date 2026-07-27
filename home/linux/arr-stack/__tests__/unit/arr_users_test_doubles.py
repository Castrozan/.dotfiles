import sys
from pathlib import Path

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import user_account_operations

FRIEND_USER = {
    "Id": "friend-id",
    "Name": "Rogerio",
    "Policy": {"IsAdministrator": False},
}
ADMIN_USER = {"Id": "admin-id", "Name": "lucas", "Policy": {"IsAdministrator": True}}

DECLARED_LIBRARIES = [
    {"Name": "Movies", "ItemId": "movies-id"},
    {"Name": "TV", "ItemId": "tv-id"},
    {"Name": "Movies (Private)", "ItemId": "movies-private-id"},
    {"Name": "TV (Private)", "ItemId": "tv-private-id"},
]
PUBLIC_LIBRARY_IDS = ["movies-id", "tv-id"]


def make_context():
    return user_account_operations.ArrUsersContext(
        jellyfin_base_url="http://jellyfin",
        jellyfin_api_key="jellyfin-key",
        jellyseerr_base_url="http://jellyseerr",
        jellyseerr_api_key="jellyseerr-key",
    )


def stub_jellyfin(monkeypatch, users, created_user=None, libraries=None):
    calls = {"policies": [], "deleted": [], "passwords": [], "created": []}
    available_libraries = DECLARED_LIBRARIES if libraries is None else libraries

    def find_user_by_name(base_url, api_key, username):
        for user in users:
            if user["Name"].lower() == username.lower():
                return user
        return None

    def create_user(base_url, api_key, username, password):
        calls["created"].append((username, password))
        return created_user

    monkeypatch.setattr(
        user_account_operations.jellyfin_api_client,
        "find_user_by_name",
        find_user_by_name,
    )
    monkeypatch.setattr(
        user_account_operations.jellyfin_api_client, "create_user", create_user
    )
    monkeypatch.setattr(
        user_account_operations.jellyfin_api_client,
        "update_user_policy",
        lambda base_url, api_key, user_id, policy: calls["policies"].append(
            (user_id, policy)
        ),
    )
    monkeypatch.setattr(
        user_account_operations.jellyfin_api_client,
        "delete_user",
        lambda base_url, api_key, user_id: calls["deleted"].append(user_id),
    )
    monkeypatch.setattr(
        user_account_operations.jellyfin_api_client,
        "set_user_password",
        lambda base_url, api_key, user_id, password: calls["passwords"].append(
            (user_id, password)
        ),
    )
    monkeypatch.setattr(
        user_account_operations.jellyfin_api_client,
        "list_virtual_folders",
        lambda base_url, api_key: available_libraries,
    )
    return calls


def stub_jellyseerr(monkeypatch, jellyseerr_user=None):
    calls = {"imported": [], "deleted": [], "permissions": [], "emails": []}
    monkeypatch.setattr(
        user_account_operations.jellyseerr_api_client,
        "import_jellyfin_users",
        lambda base_url, api_key, user_ids: calls["imported"].append(user_ids),
    )
    monkeypatch.setattr(
        user_account_operations.jellyseerr_api_client,
        "find_user_by_jellyfin_user_id",
        lambda base_url, api_key, user_id: jellyseerr_user,
    )
    monkeypatch.setattr(
        user_account_operations.jellyseerr_api_client,
        "delete_user",
        lambda base_url, api_key, user_id: calls["deleted"].append(user_id),
    )
    monkeypatch.setattr(
        user_account_operations.jellyseerr_api_client,
        "set_user_permissions",
        lambda base_url, api_key, user_id, permissions: calls["permissions"].append(
            (user_id, permissions)
        ),
    )
    monkeypatch.setattr(
        user_account_operations.jellyseerr_api_client,
        "set_user_email",
        lambda base_url, api_key, user_id, email: calls["emails"].append(
            (user_id, email)
        ),
    )
    return calls
