from arr_api_client import wait_for_api_ready
from provisioner_logging import log
from runtime_config import load_desired_objects, read_app_api_key
from upsert_engine import upsert_resource

APP_API_VERSION = {"radarr": "v3", "sonarr": "v3", "prowlarr": "v1"}

RESOURCE_PLAN = [
    {
        "app": "radarr",
        "port": 7878,
        "resource": "downloadclient",
        "match": "name",
        "update": True,
        "force_save": True,
    },
    {
        "app": "radarr",
        "port": 7878,
        "resource": "rootfolder",
        "match": "path",
        "update": False,
        "force_save": False,
    },
    {
        "app": "radarr",
        "port": 7878,
        "resource": "customformat",
        "match": "name",
        "update": True,
        "force_save": False,
    },
    {
        "app": "sonarr",
        "port": 8989,
        "resource": "downloadclient",
        "match": "name",
        "update": True,
        "force_save": True,
    },
    {
        "app": "sonarr",
        "port": 8989,
        "resource": "rootfolder",
        "match": "path",
        "update": False,
        "force_save": False,
    },
    {
        "app": "prowlarr",
        "port": 9696,
        "resource": "indexer",
        "match": "name",
        "update": True,
        "force_save": True,
    },
]


def build_base_url(bind_address, port, app):
    return f"http://{bind_address}:{port}/api/{APP_API_VERSION[app]}"


def provision_step(configuration, step, dry_run):
    app = step["app"]
    base_url = build_base_url(configuration["bind_address"], step["port"], app)
    api_key = read_app_api_key(configuration["config_root"], app)
    if not wait_for_api_ready(base_url, api_key):
        raise RuntimeError(f"{app} api not reachable")
    desired_objects = load_desired_objects(
        configuration["desired_state_dir"],
        app,
        step["resource"],
        configuration["secret_map"],
    )
    outcomes = upsert_resource(
        base_url,
        api_key,
        step["resource"],
        desired_objects,
        step["match"],
        step["update"],
        step["force_save"],
        dry_run,
    )
    log(f"{app}/{step['resource']}: {outcomes}")


def provision_all(configuration, dry_run):
    failed_steps = 0
    for step in RESOURCE_PLAN:
        try:
            provision_step(configuration, step, dry_run)
        except Exception as error:
            failed_steps += 1
            log(f"{step['app']}/{step['resource']}: skipped after error: {error}")
    if failed_steps:
        log(
            f"WARNING: {failed_steps} of {len(RESOURCE_PLAN)} steps could not be applied; "
            "config was not fully reconciled this run"
        )
    return failed_steps
