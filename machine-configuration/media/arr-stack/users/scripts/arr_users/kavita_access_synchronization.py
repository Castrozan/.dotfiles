import kavita_account_policy
import kavita_api_client
import kavita_library_declaration
import kavita_library_source_folders
import runtime_credentials


def reconcile_library_source_folders(context, kavita_libraries):
    reconciled_library_name = runtime_credentials.kavita_source_folder_library_name()
    source_library_folders = (
        kavita_library_source_folders.resolve_source_library_folders()
    )
    if not reconciled_library_name or not source_library_folders:
        return []
    repointed_library_names = []
    for library in kavita_libraries:
        if library.get("name") != reconciled_library_name:
            continue
        if kavita_library_source_folders.library_already_points_at_sources(
            library, source_library_folders
        ):
            continue
        kavita_api_client.update_library(
            context.kavita_base_url,
            context.kavita_bearer_token,
            kavita_library_source_folders.build_library_source_folder_update(
                library, source_library_folders
            ),
        )
        repointed_library_names.append(library.get("name"))
    return repointed_library_names


def reconcile_account_library_access(context, kavita_users, kavita_libraries):
    reconciled_usernames = []
    for kavita_user in kavita_users:
        username = kavita_user.get("username")
        kavita_api_client.update_account(
            context.kavita_base_url,
            context.kavita_bearer_token,
            kavita_account_policy.build_account_library_access_update(
                kavita_user,
                kavita_library_declaration.resolve_visible_library_ids(
                    kavita_libraries, username
                ),
                kavita_library_declaration.account_sees_every_library(username),
            ),
        )
        reconciled_usernames.append(username)
    return reconciled_usernames


def synchronize_kavita_library_access(context):
    bearer_token = kavita_api_client.wait_for_bearer_token(
        context.kavita_base_url, context.kavita_api_key
    )
    if bearer_token is None:
        raise ValueError(
            f"Kavita at {context.kavita_base_url} never became reachable; "
            "the friend library boundary was left as it already is"
        )
    context.kavita_bearer_token = bearer_token
    kavita_libraries = kavita_api_client.list_libraries(
        context.kavita_base_url, bearer_token
    )
    kavita_users = kavita_api_client.list_users(context.kavita_base_url, bearer_token)
    reconciled_account_usernames = reconcile_account_library_access(
        context, kavita_users, kavita_libraries
    )
    repointed_library_names = reconcile_library_source_folders(
        context, kavita_libraries
    )
    return {
        "public_libraries": kavita_library_declaration.public_library_names(),
        "private_libraries": kavita_library_declaration.private_library_names_present(
            kavita_libraries
        ),
        "privileged_accounts": list(
            kavita_library_declaration.privileged_account_usernames()
        ),
        "undeclared_accounts": kavita_library_declaration.undeclared_account_usernames(
            kavita_users
        ),
        "reconciled_accounts": reconciled_account_usernames,
        "repointed_libraries": repointed_library_names,
    }
