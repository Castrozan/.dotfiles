import urllib.error
from dataclasses import dataclass

import friend_account_policy
import jellyfin_api_client
import jellyseerr_api_client
import password_generation


@dataclass
class ArrUsersContext:
    jellyfin_base_url: str
    jellyfin_api_key: str
    jellyseerr_base_url: str
    jellyseerr_api_key: str


def require_existing_user(context, username):
    jellyfin_user = jellyfin_api_client.find_user_by_name(
        context.jellyfin_base_url, context.jellyfin_api_key, username
    )
    if jellyfin_user is None:
        raise ValueError(f"no Jellyfin user named '{username}'")
    return jellyfin_user


def require_friend_user(context, username):
    jellyfin_user = require_existing_user(context, username)
    if friend_account_policy.is_administrator(jellyfin_user):
        raise ValueError(
            f"'{username}' is a Jellyfin administrator; refusing to modify it"
        )
    return jellyfin_user


def list_accounts(context):
    jellyseerr_users = jellyseerr_api_client.list_users(
        context.jellyseerr_base_url, context.jellyseerr_api_key
    )
    jellyseerr_by_jellyfin_id = {
        user.get("jellyfinUserId"): user for user in jellyseerr_users
    }
    accounts = []
    for jellyfin_user in jellyfin_api_client.list_users(
        context.jellyfin_base_url, context.jellyfin_api_key
    ):
        jellyfin_user_id = jellyfin_user.get("Id")
        jellyseerr_user = jellyseerr_by_jellyfin_id.get(jellyfin_user_id)
        accounts.append(
            {
                "username": jellyfin_user.get("Name"),
                "jellyfin_user_id": jellyfin_user_id,
                "is_administrator": friend_account_policy.is_administrator(
                    jellyfin_user
                ),
                "is_disabled": bool(jellyfin_user.get("Policy", {}).get("IsDisabled")),
                "jellyseerr_user_id": (
                    jellyseerr_user.get("id") if jellyseerr_user else None
                ),
            }
        )
    return accounts


def create_friend_account(context, username, password=None):
    existing_user = jellyfin_api_client.find_user_by_name(
        context.jellyfin_base_url, context.jellyfin_api_key, username
    )
    if existing_user is not None:
        raise ValueError(f"Jellyfin user '{username}' already exists")

    friend_password = password or password_generation.generate_friend_password()
    created_user = jellyfin_api_client.create_user(
        context.jellyfin_base_url, context.jellyfin_api_key, username, friend_password
    )
    jellyfin_user_id = created_user["Id"]

    apply_friend_policy_or_roll_back_user(context, created_user)
    jellyseerr_user_id = import_into_jellyseerr_best_effort(context, jellyfin_user_id)

    return {
        "username": username,
        "password": friend_password,
        "jellyfin_user_id": jellyfin_user_id,
        "jellyseerr_user_id": jellyseerr_user_id,
    }


def apply_friend_policy_or_roll_back_user(context, created_user):
    friend_policy = friend_account_policy.build_friend_policy(
        created_user.get("Policy", {})
    )
    try:
        jellyfin_api_client.update_user_policy(
            context.jellyfin_base_url,
            context.jellyfin_api_key,
            created_user["Id"],
            friend_policy,
        )
    except urllib.error.URLError:
        jellyfin_api_client.delete_user(
            context.jellyfin_base_url, context.jellyfin_api_key, created_user["Id"]
        )
        raise


def import_into_jellyseerr_best_effort(context, jellyfin_user_id):
    try:
        jellyseerr_api_client.import_jellyfin_users(
            context.jellyseerr_base_url, context.jellyseerr_api_key, [jellyfin_user_id]
        )
        jellyseerr_user = jellyseerr_api_client.find_user_by_jellyfin_user_id(
            context.jellyseerr_base_url, context.jellyseerr_api_key, jellyfin_user_id
        )
    except urllib.error.URLError:
        return None
    return jellyseerr_user.get("id") if jellyseerr_user else None


def delete_friend_account(context, username):
    jellyfin_user = require_friend_user(context, username)
    jellyfin_user_id = jellyfin_user["Id"]

    jellyseerr_user = jellyseerr_api_client.find_user_by_jellyfin_user_id(
        context.jellyseerr_base_url, context.jellyseerr_api_key, jellyfin_user_id
    )
    if jellyseerr_user is not None:
        jellyseerr_api_client.delete_user(
            context.jellyseerr_base_url,
            context.jellyseerr_api_key,
            jellyseerr_user["id"],
        )

    jellyfin_api_client.delete_user(
        context.jellyfin_base_url, context.jellyfin_api_key, jellyfin_user_id
    )
    return {"username": username, "jellyfin_user_id": jellyfin_user_id}


def reset_friend_password(context, username, password=None):
    jellyfin_user = require_friend_user(context, username)
    friend_password = password or password_generation.generate_friend_password()
    jellyfin_api_client.set_user_password(
        context.jellyfin_base_url,
        context.jellyfin_api_key,
        jellyfin_user["Id"],
        friend_password,
    )
    return {"username": username, "password": friend_password}


def set_friend_account_enabled(context, username, enabled):
    jellyfin_user = require_friend_user(context, username)
    updated_policy = friend_account_policy.build_enabled_state_policy(
        jellyfin_user.get("Policy", {}), enabled
    )
    jellyfin_api_client.update_user_policy(
        context.jellyfin_base_url,
        context.jellyfin_api_key,
        jellyfin_user["Id"],
        updated_policy,
    )
    return {"username": username, "enabled": enabled}
