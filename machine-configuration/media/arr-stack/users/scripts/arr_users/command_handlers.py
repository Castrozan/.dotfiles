import account_permission_synchronization
import kavita_access_synchronization
import library_access_synchronization
import private_request_routing
import request_routing_synchronization
import user_account_operations


def print_accounts(accounts):
    for account in accounts:
        role = "admin" if account["is_administrator"] else "friend"
        state = "disabled" if account["is_disabled"] else "enabled"
        requests_state = (
            "jellyseerr" if account["jellyseerr_user_id"] else "no-jellyseerr"
        )
        print(f"{account['username']}\t{role}\t{state}\t{requests_state}")


def run_list(context, _arguments):
    print_accounts(user_account_operations.list_accounts(context))


def run_create(context, arguments):
    created = user_account_operations.create_friend_account(
        context, arguments.username, arguments.password, arguments.email
    )
    print(f"username: {created['username']}")
    print(f"password: {created['password']}")
    print(f"jellyfin: {created['jellyfin_user_id']}")
    print(f"jellyseerr: {created['jellyseerr_user_id'] or 'import pending'}")
    if arguments.email and created["jellyseerr_user_id"] is not None:
        print(f"email: {arguments.email}")


def run_set_email(context, arguments):
    updated = user_account_operations.set_friend_email(
        context, arguments.username, arguments.email
    )
    print(f"username: {updated['username']}")
    print(f"email: {updated['email']}")


def run_delete(context, arguments):
    deleted = user_account_operations.delete_friend_account(context, arguments.username)
    print(f"deleted {deleted['username']}")


def run_reset_password(context, arguments):
    reset = user_account_operations.reset_friend_password(
        context, arguments.username, arguments.password
    )
    print(f"username: {reset['username']}")
    print(f"password: {reset['password']}")


def run_enable(context, arguments):
    user_account_operations.set_friend_account_enabled(
        context, arguments.username, True
    )
    print(f"enabled {arguments.username}")


def run_disable(context, arguments):
    user_account_operations.set_friend_account_enabled(
        context, arguments.username, False
    )
    print(f"disabled {arguments.username}")


def run_sync(context, _arguments):
    synchronized = library_access_synchronization.synchronize_library_access(context)
    print(
        f"created libraries: {', '.join(synchronized['created_libraries']) or 'none'}"
    )
    print(f"every account can see: {', '.join(synchronized['public_libraries'])}")
    print(
        f"private libraries: {', '.join(synchronized['private_libraries']) or 'none'}"
    )
    print(
        "only these accounts see them: "
        f"{', '.join(synchronized['private_library_accounts']) or 'none'}"
    )
    print(f"reconciled: {', '.join(synchronized['reconciled_accounts']) or 'none'}")
    failed_library_names = synchronized["failed_libraries"]
    if failed_library_names:
        raise ValueError(
            "friend visibility was reconciled, but Jellyfin refused to create "
            f"{', '.join(failed_library_names)}; the usual cause is the backing "
            "media directory not existing yet"
        )


def run_sync_kavita_access(context, _arguments):
    synchronized = kavita_access_synchronization.synchronize_kavita_library_access(
        context
    )
    print(f"every account can read: {', '.join(synchronized['public_libraries'])}")
    print(
        "withheld from friends: "
        f"{', '.join(synchronized['private_libraries']) or 'none'}"
    )
    print(
        "only these accounts read them: "
        f"{', '.join(synchronized['privileged_accounts']) or 'none'}"
    )
    print(f"repointed: {', '.join(synchronized['repointed_libraries']) or 'none'}")
    print(f"reconciled: {', '.join(synchronized['reconciled_accounts']) or 'none'}")
    undeclared_usernames = synchronized["undeclared_accounts"]
    if undeclared_usernames:
        print(
            "registered without being declared, holding public access only: "
            f"{', '.join(undeclared_usernames)}"
        )


def run_sync_request_routing(context, _arguments):
    synchronized = request_routing_synchronization.synchronize_request_routing(context)
    if synchronized["routed_account"] is None:
        print(
            f"no {private_request_routing.PRIVATE_REQUEST_ACCOUNT_USERNAME} account "
            "exists, so no request routes privately yet"
        )
        return
    print(f"routing every request from: {synchronized['routed_account']}")
    print(f"created rules: {', '.join(synchronized['created_rules']) or 'none'}")
    print(f"updated rules: {', '.join(synchronized['updated_rules']) or 'none'}")
    print(f"removed rules: {', '.join(synchronized['removed_rules']) or 'none'}")


def run_sync_account_permissions(context, _arguments):
    synchronized = account_permission_synchronization.synchronize_account_permissions(
        context
    )
    print(f"administered by: {', '.join(synchronized['administrator_accounts'])}")
    print(
        "requesting without approval: "
        f"{', '.join(synchronized['self_approving_accounts']) or 'none'}"
    )
    print(f"rewritten: {', '.join(synchronized['rewritten_accounts']) or 'none'}")


COMMAND_HANDLERS = {
    "list": run_list,
    "sync": run_sync,
    "sync-kavita-access": run_sync_kavita_access,
    "sync-request-routing": run_sync_request_routing,
    "sync-account-permissions": run_sync_account_permissions,
    "create": run_create,
    "set-email": run_set_email,
    "delete": run_delete,
    "reset-password": run_reset_password,
    "enable": run_enable,
    "disable": run_disable,
}
