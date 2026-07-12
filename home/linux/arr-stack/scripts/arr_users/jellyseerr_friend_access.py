import urllib.error

import friend_account_policy
import jellyseerr_api_client


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
    apply_jellyseerr_friend_policy(context, jellyseerr_user["id"], email)
    return jellyseerr_user["id"]


def apply_jellyseerr_friend_policy(context, jellyseerr_user_id, email=None):
    jellyseerr_api_client.set_user_permissions(
        context.jellyseerr_base_url,
        context.jellyseerr_api_key,
        jellyseerr_user_id,
        friend_account_policy.FRIEND_JELLYSEERR_PERMISSIONS_BITMASK,
    )
    if email:
        jellyseerr_api_client.set_user_email(
            context.jellyseerr_base_url,
            context.jellyseerr_api_key,
            jellyseerr_user_id,
            email,
        )
