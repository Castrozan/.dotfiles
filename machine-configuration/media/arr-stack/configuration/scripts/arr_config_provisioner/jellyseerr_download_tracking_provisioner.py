from arr_api_client import request_json
from provisioner_logging import log


def provision_server_download_tracking(base_url, api_key, server_type, dry_run):
    settings_url = f"{base_url}/api/v1/settings/{server_type}"
    servers = request_json("GET", settings_url, api_key) or []
    outcomes = []
    for server in servers:
        if server.get("syncEnabled") is True:
            outcomes.append("unchanged")
            continue
        if dry_run:
            log(
                f"[dry-run] jellyseerr/{server_type} '{server['name']}': would enable tracking"
            )
            outcomes.append("would-update")
            continue
        settings = {field: value for field, value in server.items() if field != "id"}
        settings["syncEnabled"] = True
        request_json("PUT", f"{settings_url}/{server['id']}", api_key, settings)
        outcomes.append("updated")
    return outcomes
