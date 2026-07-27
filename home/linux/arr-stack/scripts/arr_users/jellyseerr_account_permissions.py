import friend_account_policy

JELLYSEERR_OWNER_ACCOUNT_ID = 1

JELLYSEERR_ADMINISTRATOR_ACCOUNT_USERNAMES = ("jellyseerr",)

SELF_APPROVING_REQUESTER_PERMISSIONS = (
    friend_account_policy.FRIEND_JELLYSEERR_PERMISSIONS_BITMASK
)


def resolve_account_names(jellyseerr_user):
    return {
        account_name
        for account_name in (
            jellyseerr_user.get("displayName"),
            jellyseerr_user.get("jellyfinUsername"),
            jellyseerr_user.get("username"),
        )
        if account_name
    }


def describe_account(jellyseerr_user):
    return (
        jellyseerr_user.get("jellyfinUsername")
        or jellyseerr_user.get("displayName")
        or jellyseerr_user.get("username")
        or f"jellyseerr user {jellyseerr_user.get('id')}"
    )


def account_administers_jellyseerr(jellyseerr_user):
    if int(jellyseerr_user.get("id") or 0) == JELLYSEERR_OWNER_ACCOUNT_ID:
        return True
    return not resolve_account_names(jellyseerr_user).isdisjoint(
        JELLYSEERR_ADMINISTRATOR_ACCOUNT_USERNAMES
    )


def account_requests_without_approval(jellyseerr_user):
    return (
        int(jellyseerr_user.get("permissions") or 0)
        == SELF_APPROVING_REQUESTER_PERMISSIONS
    )


def administrator_accounts(jellyseerr_users):
    return [
        jellyseerr_user
        for jellyseerr_user in jellyseerr_users
        if account_administers_jellyseerr(jellyseerr_user)
    ]


def self_approving_accounts(jellyseerr_users):
    return [
        jellyseerr_user
        for jellyseerr_user in jellyseerr_users
        if not account_administers_jellyseerr(jellyseerr_user)
    ]


def accounts_needing_permission_rewrite(jellyseerr_users):
    return [
        jellyseerr_user
        for jellyseerr_user in self_approving_accounts(jellyseerr_users)
        if not account_requests_without_approval(jellyseerr_user)
    ]
