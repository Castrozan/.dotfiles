import urllib.error

from jellyseerr import jellyseerr_account_permissions
from jellyseerr import jellyseerr_api_client


def import_into_jellyseerr_best_effort(context, jellyfin_user_id, email=None):
    try:
        jellyseerr_api_client.import_jellyfin_users(
            context.jellyseerr_base_url, context.jellyseerr_api_key, [jellyfin_user_id]
        )
        jellyseerr_user = jellyseerr_api_client.find_user_by_jellyfin_user_id(
            context.jellyseerr_base_url, context.jellyseerr_api_key, jellyfin_user_id
        )
    except urllib.error.URLError:
        return None
    if jellyseerr_user is None:
        return None
    apply_jellyseerr_friend_policy(context, jellyseerr_user, email)
    return jellyseerr_user["id"]


def apply_jellyseerr_friend_policy(context, jellyseerr_user, email=None):
    jellyseerr_api_client.set_user_permissions(
        context.jellyseerr_base_url,
        context.jellyseerr_api_key,
        jellyseerr_user["id"],
        jellyseerr_account_permissions.desired_requester_permissions(jellyseerr_user),
    )
    if email:
        jellyseerr_api_client.set_user_email(
            context.jellyseerr_base_url,
            context.jellyseerr_api_key,
            jellyseerr_user["id"],
            email,
        )
