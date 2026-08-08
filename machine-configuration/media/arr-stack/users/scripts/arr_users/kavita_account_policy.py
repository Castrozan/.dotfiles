PRIVILEGED_KAVITA_ROLES = (
    "Admin",
    "Promote",
    "ChangeRestriction",
)

UNRESTRICTED_AGE_RESTRICTION = {"ageRating": 0, "includeUnknowns": True}


def build_friend_roles(current_roles):
    return [
        role_name
        for role_name in current_roles
        if role_name not in PRIVILEGED_KAVITA_ROLES
    ]


def build_account_library_access_update(
    kavita_user, visible_library_ids, keeps_privileged_roles
):
    current_roles = list(kavita_user.get("roles") or [])
    return {
        "userId": kavita_user.get("id"),
        "username": kavita_user.get("username"),
        "roles": current_roles
        if keeps_privileged_roles
        else build_friend_roles(current_roles),
        "libraries": list(visible_library_ids),
        "ageRestriction": kavita_user.get("ageRestriction")
        or dict(UNRESTRICTED_AGE_RESTRICTION),
    }
