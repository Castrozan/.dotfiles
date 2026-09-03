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


def upsert_desired_object(
    base_url,
    api_key,
    resource,
    current,
    desired,
    key_value,
    supports_update,
    force_save,
    dry_run,
):
    if current is None:
        return create_missing_object(
            base_url, api_key, resource, desired, key_value, force_save, dry_run
        )
    if supports_update:
        return update_existing_object(
            base_url,
            api_key,
            resource,
            current,
            desired,
            key_value,
            force_save,
            dry_run,
        )
    log(f"{resource} '{key_value}': present, left as is")
    return "unchanged"


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
    failed_keys = []
    for desired in desired_objects:
        key_value = desired.get(match_key)
        if contains_unresolved_secret_token(desired):
            log(f"{resource} '{key_value}': skipped, a required secret is not provided")
            outcomes.append("skipped-missing-secret")
            continue
        current = existing_by_key.get(key_value)
        try:
            outcomes.append(
                upsert_desired_object(
                    base_url,
                    api_key,
                    resource,
                    current,
                    desired,
                    key_value,
                    supports_update,
                    force_save,
                    dry_run,
                )
            )
        except Exception as error:
            failed_keys.append(key_value)
            outcomes.append("failed")
            log(f"{resource} '{key_value}': failed: {error}")
    if failed_keys:
        failed_key_list = ", ".join(str(key) for key in failed_keys)
        raise RuntimeError(
            f"{len(failed_keys)} of {len(desired_objects)} {resource} objects failed: "
            f"{failed_key_list}"
        )
    return outcomes
