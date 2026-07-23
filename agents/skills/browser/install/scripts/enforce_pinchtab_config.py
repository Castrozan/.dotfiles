import json
import os
import secrets
import sys
import tempfile

pinchtab_config_path = os.path.expanduser("~/.pinchtab/config.json")

full_access_security_and_headed_default_policy = {
    "security": {
        "allowEvaluate": True,
        "allowMacro": True,
        "allowScreencast": True,
        "allowDownload": True,
        "allowCookies": True,
        "allowNetworkIntercept": True,
        "allowUpload": True,
        "allowClipboard": True,
        "allowStateExport": True,
        "enableActionGuards": False,
        "allowedDomains": ["*"],
        "downloadAllowedDomains": ["*"],
        "maxRedirects": -1,
        "attach": {
            "enabled": True,
            "allowHosts": ["*"],
            "allowSchemes": ["ws", "wss"],
        },
        "idpi": {
            "enabled": False,
            "strictMode": False,
            "scanContent": False,
            "wrapContent": False,
        },
    },
    "instanceDefaults": {
        "mode": "headed",
    },
}


def merge_enforced_leaves_preserving_everything_else(current_config, enforced_policy):
    for key, enforced_value in enforced_policy.items():
        current_value = current_config.get(key)
        if isinstance(enforced_value, dict) and isinstance(current_value, dict):
            merge_enforced_leaves_preserving_everything_else(
                current_value, enforced_value
            )
        else:
            current_config[key] = enforced_value
    return current_config


def load_existing_config_tolerating_absence_but_never_clobbering_corruption(path):
    if not os.path.exists(path):
        return {}
    with open(path) as config_handle:
        return json.load(config_handle)


def ensure_server_bearer_token_exists_so_a_fresh_machine_starts_authenticated(config):
    server = config.get("server")
    if not isinstance(server, dict):
        server = {}
        config["server"] = server
    if not server.get("token"):
        server["token"] = secrets.token_hex(24)


def atomically_write_config_with_owner_only_permissions(path, config):
    directory = os.path.dirname(path)
    temporary_descriptor, temporary_path = tempfile.mkstemp(
        dir=directory, prefix=".config.", suffix=".json"
    )
    with os.fdopen(temporary_descriptor, "w") as temporary_handle:
        json.dump(config, temporary_handle, indent=2)
    os.chmod(temporary_path, 0o600)
    os.replace(temporary_path, path)


def main():
    directory = os.path.dirname(pinchtab_config_path)
    os.makedirs(directory, exist_ok=True)
    try:
        config = (
            load_existing_config_tolerating_absence_but_never_clobbering_corruption(
                pinchtab_config_path
            )
        )
    except json.JSONDecodeError:
        print(
            f"enforce-pinchtab-config: {pinchtab_config_path} is not valid JSON; leaving it untouched so the "
            "server-owned token and machine paths are never destroyed, and skipping enforcement this rebuild",
            file=sys.stderr,
        )
        return
    if not isinstance(config, dict):
        print(
            f"enforce-pinchtab-config: {pinchtab_config_path} is valid JSON but not an object; leaving it "
            "untouched and skipping enforcement this rebuild rather than aborting the whole activation",
            file=sys.stderr,
        )
        return
    serialized_before = json.dumps(config, sort_keys=True)
    merge_enforced_leaves_preserving_everything_else(
        config, full_access_security_and_headed_default_policy
    )
    ensure_server_bearer_token_exists_so_a_fresh_machine_starts_authenticated(config)
    if json.dumps(config, sort_keys=True) == serialized_before:
        return
    atomically_write_config_with_owner_only_permissions(pinchtab_config_path, config)
    print(
        "enforce-pinchtab-config: reasserted full-capability, all-hosts, headed-default policy into "
        f"{pinchtab_config_path} (a running server needs `pinchtab server restart` to pick it up)"
    )


if __name__ == "__main__":
    main()
