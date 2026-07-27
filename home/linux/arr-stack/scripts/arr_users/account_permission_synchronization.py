import jellyseerr_account_permissions
import jellyseerr_api_client


def synchronize_account_permissions(context):
    jellyseerr_users = jellyseerr_api_client.list_users(
        context.jellyseerr_base_url, context.jellyseerr_api_key
    )
    administrators = jellyseerr_account_permissions.administrator_accounts(
        jellyseerr_users
    )
    if not administrators:
        raise ValueError(
            "refusing to rewrite Jellyseerr account permissions while no declared "
            "administrator account exists, because every remaining account would be "
            "left unable to reach Jellyseerr settings, users and override rules and "
            "nobody could grant the permission back through the web UI"
        )
    rewritten_accounts = (
        jellyseerr_account_permissions.accounts_needing_permission_rewrite(
            jellyseerr_users
        )
    )
    if rewritten_accounts:
        jellyseerr_api_client.set_accounts_permissions(
            context.jellyseerr_base_url,
            context.jellyseerr_api_key,
            [jellyseerr_user["id"] for jellyseerr_user in rewritten_accounts],
            jellyseerr_account_permissions.SELF_APPROVING_REQUESTER_PERMISSIONS,
        )
    return {
        "administrator_accounts": [
            jellyseerr_account_permissions.describe_account(jellyseerr_user)
            for jellyseerr_user in administrators
        ],
        "self_approving_accounts": [
            jellyseerr_account_permissions.describe_account(jellyseerr_user)
            for jellyseerr_user in jellyseerr_account_permissions.self_approving_accounts(
                jellyseerr_users
            )
        ],
        "rewritten_accounts": [
            jellyseerr_account_permissions.describe_account(jellyseerr_user)
            for jellyseerr_user in rewritten_accounts
        ],
    }
