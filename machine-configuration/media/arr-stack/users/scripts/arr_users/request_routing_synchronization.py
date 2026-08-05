import jellyseerr_account_permissions
import jellyseerr_api_client
import private_request_routing


def find_private_request_account(context):
    for jellyseerr_user in jellyseerr_api_client.list_users(
        context.jellyseerr_base_url, context.jellyseerr_api_key
    ):
        if (
            private_request_routing.PRIVATE_REQUEST_ACCOUNT_USERNAME
            in jellyseerr_account_permissions.resolve_account_names(jellyseerr_user)
        ):
            return jellyseerr_user
    return None


def resolve_default_service_indexes(context):
    service_indexes = {}
    for service_name in ("radarr", "sonarr"):
        service_indexes[service_name] = private_request_routing.default_service_index(
            jellyseerr_api_client.list_service_servers(
                context.jellyseerr_base_url, context.jellyseerr_api_key, service_name
            )
        )
    missing_service_names = [
        service_name for service_name, index in service_indexes.items() if index is None
    ]
    if missing_service_names:
        raise ValueError(
            "refusing to write a private request route while Jellyseerr has no default "
            f"non-4k server for: {', '.join(sorted(missing_service_names))}; requests "
            "would silently keep landing in the public root folder"
        )
    return service_indexes


def apply_desired_override_rules(context, desired_override_rules):
    existing_private_rules = {
        private_request_routing.override_rule_slot(override_rule): override_rule
        for override_rule in jellyseerr_api_client.list_override_rules(
            context.jellyseerr_base_url, context.jellyseerr_api_key
        )
        if private_request_routing.routes_to_a_private_root_folder(override_rule)
    }
    created_rules, updated_rules, desired_slots = [], [], set()
    for desired_override_rule in desired_override_rules:
        slot = private_request_routing.override_rule_slot(desired_override_rule)
        desired_slots.add(slot)
        existing_override_rule = existing_private_rules.get(slot)
        description = private_request_routing.describe_override_rule(
            desired_override_rule
        )
        if existing_override_rule is None:
            jellyseerr_api_client.create_override_rule(
                context.jellyseerr_base_url,
                context.jellyseerr_api_key,
                desired_override_rule,
            )
            created_rules.append(description)
        elif not private_request_routing.override_rule_already_applied(
            existing_override_rule, desired_override_rule
        ):
            jellyseerr_api_client.update_override_rule(
                context.jellyseerr_base_url,
                context.jellyseerr_api_key,
                existing_override_rule["id"],
                desired_override_rule,
            )
            updated_rules.append(description)
    removed_rules = []
    for slot, existing_override_rule in existing_private_rules.items():
        if slot in desired_slots:
            continue
        jellyseerr_api_client.delete_override_rule(
            context.jellyseerr_base_url,
            context.jellyseerr_api_key,
            existing_override_rule["id"],
        )
        removed_rules.append(
            private_request_routing.describe_override_rule(existing_override_rule)
        )
    return created_rules, updated_rules, removed_rules


def synchronize_request_routing(context):
    private_request_account = find_private_request_account(context)
    if private_request_account is None:
        return {
            "routed_account": None,
            "created_rules": [],
            "updated_rules": [],
            "removed_rules": [],
        }
    if not private_request_routing.account_requests_can_be_overridden(
        private_request_account.get("permissions")
    ):
        raise ValueError(
            f"{private_request_routing.PRIVATE_REQUEST_ACCOUNT_USERNAME} holds the "
            "Jellyseerr admin or manage-requests permission, which makes Jellyseerr "
            "skip every override rule, so its requests would land in the public root "
            "folder while looking correctly configured; drop those permissions first"
        )
    service_indexes = resolve_default_service_indexes(context)
    created_rules, updated_rules, removed_rules = apply_desired_override_rules(
        context,
        private_request_routing.build_desired_override_rules(
            private_request_account["id"],
            service_indexes["radarr"],
            service_indexes["sonarr"],
        ),
    )
    return {
        "routed_account": private_request_routing.PRIVATE_REQUEST_ACCOUNT_USERNAME,
        "created_rules": created_rules,
        "updated_rules": updated_rules,
        "removed_rules": removed_rules,
    }
