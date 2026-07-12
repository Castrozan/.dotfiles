from arr_api_client import get_host_config, update_host_config
from provisioner_logging import log


def build_forms_authenticated_host_config(current_host_config, username, password):
    return {
        **current_host_config,
        "authenticationMethod": "forms",
        "authenticationRequired": "enabled",
        "username": username,
        "password": password,
        "passwordConfirmation": password,
    }


def provision_host_login(base_url, api_key, username, password, dry_run):
    if not username or not password:
        log("host-auth: skipped, username or password not provided")
        return "skipped-missing-secret"
    current_host_config = get_host_config(base_url, api_key)
    desired_host_config = build_forms_authenticated_host_config(
        current_host_config, username, password
    )
    if dry_run:
        log(f"host-auth: would set forms login for '{username}'")
        return "would-update"
    update_host_config(base_url, api_key, desired_host_config)
    log(f"host-auth: forms login set for '{username}'")
    return "updated"
