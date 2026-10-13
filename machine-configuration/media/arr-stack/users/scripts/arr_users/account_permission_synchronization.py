from jellyseerr import jellyseerr_account_permissions
from jellyseerr import jellyseerr_api_client


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
    accounts_by_permissions = {}
    for jellyseerr_user in rewritten_accounts:
        permissions = jellyseerr_account_permissions.desired_requester_permissions(
            jellyseerr_user
        )
        accounts_by_permissions.setdefault(permissions, []).append(
            jellyseerr_user["id"]
        )
    for permissions, account_ids in accounts_by_permissions.items():
        jellyseerr_api_client.set_accounts_permissions(
            context.jellyseerr_base_url,
            context.jellyseerr_api_key,
            account_ids,
            permissions,
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
