from arr_api_client import create_resource, get_resource_list, update_resource
from provisioner_logging import log
from runtime_config import contains_unresolved_secret_token


def create_missing_object(
    base_url, api_key, resource, desired, key_value, force_save, dry_run
):
    if dry_run:
        log(f"[dry-run] {resource} '{key_value}': would create")
        return "would-create"
    create_resource(base_url, api_key, resource, desired, force_save)
    log(f"{resource} '{key_value}': created")
    return "created"


def update_existing_object(
    base_url, api_key, resource, current, desired, key_value, force_save, dry_run
):
    body = {**desired, "id": current["id"]}
    if dry_run:
        log(f"[dry-run] {resource} '{key_value}': would update id {current['id']}")
        return "would-update"
    update_resource(base_url, api_key, resource, current["id"], body, force_save)
    log(f"{resource} '{key_value}': updated")
    return "updated"


def upsert_resource(
    base_url,
    api_key,
    resource,
    desired_objects,
    match_key,
    supports_update,
    force_save,
    dry_run,
):
    existing_by_key = {
        obj.get(match_key): obj
        for obj in get_resource_list(base_url, api_key, resource)
    }
    outcomes = []
    for desired in desired_objects:
        key_value = desired.get(match_key)
        if contains_unresolved_secret_token(desired):
            log(f"{resource} '{key_value}': skipped, a required secret is not provided")
            outcomes.append("skipped-missing-secret")
            continue
        current = existing_by_key.get(key_value)
        if current is None:
            outcomes.append(
                create_missing_object(
                    base_url, api_key, resource, desired, key_value, force_save, dry_run
                )
            )
        elif supports_update:
            outcomes.append(
                update_existing_object(
                    base_url,
                    api_key,
                    resource,
                    current,
                    desired,
                    key_value,
                    force_save,
                    dry_run,
                )
            )
        else:
            log(f"{resource} '{key_value}': present, left as is")
            outcomes.append("unchanged")
    return outcomes
