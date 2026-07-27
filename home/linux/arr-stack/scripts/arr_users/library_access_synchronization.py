import friend_account_policy
import jellyfin_api_client
import jellyfin_library_declaration
import jellyfin_library_provisioning


def reconcile_library_visibility(context, jellyfin_libraries):
    reconciled_usernames = []
    for jellyfin_user in jellyfin_api_client.list_users(
        context.jellyfin_base_url, context.jellyfin_api_key
    ):
        username = jellyfin_user.get("Name")
        visible_library_ids = jellyfin_library_declaration.resolve_visible_library_ids(
            jellyfin_libraries, username
        )
        visibility_policy = friend_account_policy.build_library_visibility_policy(
            jellyfin_user.get("Policy", {}), visible_library_ids
        )
        jellyfin_api_client.update_user_policy(
            context.jellyfin_base_url,
            context.jellyfin_api_key,
            jellyfin_user["Id"],
            visibility_policy,
        )
        reconciled_usernames.append(username)
    return reconciled_usernames


def synchronize_library_access(context):
    if not jellyfin_api_client.wait_until_ready(
        context.jellyfin_base_url, context.jellyfin_api_key
    ):
        raise ValueError(
            f"Jellyfin at {context.jellyfin_base_url} never became reachable; "
            "the private-library boundary was left as it already is"
        )
    created_library_names, failed_library_names = (
        jellyfin_library_provisioning.create_missing_declared_libraries(
            context.jellyfin_base_url, context.jellyfin_api_key
        )
    )
    jellyfin_libraries = jellyfin_api_client.list_virtual_folders(
        context.jellyfin_base_url, context.jellyfin_api_key
    )
    return {
        "created_libraries": created_library_names,
        "failed_libraries": failed_library_names,
        "public_libraries": jellyfin_library_declaration.public_library_names(),
        "private_libraries": jellyfin_library_declaration.private_library_names_present(
            jellyfin_libraries
        ),
        "private_library_accounts": list(
            jellyfin_library_declaration.PRIVATE_LIBRARY_ACCOUNT_USERNAMES
        ),
        "reconciled_accounts": reconcile_library_visibility(
            context, jellyfin_libraries
        ),
    }
