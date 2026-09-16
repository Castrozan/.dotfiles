import runtime_credentials


def public_library_names():
    return runtime_credentials.kavita_public_library_names()


def privileged_account_usernames():
    return runtime_credentials.kavita_privileged_account_usernames()


def friend_account_usernames():
    return runtime_credentials.kavita_friend_account_usernames()


def account_sees_every_library(username):
    normalized_username = (username or "").lower()
    return normalized_username in {
        privileged_username.lower()
        for privileged_username in privileged_account_usernames()
    }


def resolve_public_library_ids(kavita_libraries):
    library_id_by_name = {
        library.get("name"): library.get("id") for library in kavita_libraries
    }
    declared_public_names = public_library_names()
    missing_library_names = [
        name for name in declared_public_names if not library_id_by_name.get(name)
    ]
    if missing_library_names:
        raise ValueError(
            "refusing to write a Kavita account policy while these declared public "
            f"libraries are missing from Kavita: {', '.join(missing_library_names)}"
        )
    return [library_id_by_name[name] for name in declared_public_names]


def resolve_visible_library_ids(kavita_libraries, username):
    public_library_ids = resolve_public_library_ids(kavita_libraries)
    if not account_sees_every_library(username):
        return public_library_ids
    return [library["id"] for library in kavita_libraries if library.get("id")]


def private_library_names_present(kavita_libraries):
    declared_public_names = set(public_library_names())
    return [
        library.get("name")
        for library in kavita_libraries
        if library.get("name") not in declared_public_names
    ]


def undeclared_account_usernames(kavita_users):
    declared_usernames = {
        declared_username.lower()
        for declared_username in (
            *privileged_account_usernames(),
            *friend_account_usernames(),
        )
    }
    return [
        kavita_user.get("username")
        for kavita_user in kavita_users
        if (kavita_user.get("username") or "").lower() not in declared_usernames
    ]
