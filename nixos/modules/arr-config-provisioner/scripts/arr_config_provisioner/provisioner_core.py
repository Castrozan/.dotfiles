from arr_api_client import wait_for_api_ready
from host_auth_provisioner import provision_host_login
from provisioner_logging import log
from quality_profile_provisioner import provision_quality_profiles
from runtime_config import (
    load_desired_objects,
    load_optional_desired_objects,
    read_app_api_key,
)
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
        "app": "sonarr",
        "port": 8989,
        "resource": "customformat",
        "match": "name",
        "update": True,
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

QUALITY_PROFILE_PLAN = [
    {"app": "radarr", "port": 7878},
    {"app": "sonarr", "port": 8989},
]

HOST_LOGIN_PLAN = [
    {"app": "radarr", "port": 7878},
    {"app": "sonarr", "port": 8989},
    {"app": "prowlarr", "port": 9696},
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


def provision_quality_profile_step(configuration, step, dry_run):
    app = step["app"]
    base_url = build_base_url(configuration["bind_address"], step["port"], app)
    api_key = read_app_api_key(configuration["config_root"], app)
    if not wait_for_api_ready(base_url, api_key):
        raise RuntimeError(f"{app} api not reachable")
    desired_profiles = load_optional_desired_objects(
        configuration["desired_state_dir"],
        app,
        "qualityprofile",
        configuration["secret_map"],
    )
    if not desired_profiles:
        return
    outcomes = provision_quality_profiles(base_url, api_key, desired_profiles, dry_run)
    log(f"{app}/qualityprofile: {outcomes}")


def provision_host_login_step(configuration, step, dry_run):
    app = step["app"]
    base_url = build_base_url(configuration["bind_address"], step["port"], app)
    api_key = read_app_api_key(configuration["config_root"], app)
    if not wait_for_api_ready(base_url, api_key):
        raise RuntimeError(f"{app} api not reachable")
    outcome = provision_host_login(
        base_url,
        api_key,
        configuration["login_username"],
        configuration["login_passwords"].get(app, ""),
        dry_run,
    )
    log(f"{app}/host-login: {outcome}")


def provision_all(configuration, dry_run):
    failed_steps = 0
    total_steps = len(RESOURCE_PLAN) + len(QUALITY_PROFILE_PLAN) + len(HOST_LOGIN_PLAN)
    for step in RESOURCE_PLAN:
        try:
            provision_step(configuration, step, dry_run)
        except Exception as error:
            failed_steps += 1
            log(f"{step['app']}/{step['resource']}: skipped after error: {error}")
    for step in QUALITY_PROFILE_PLAN:
        try:
            provision_quality_profile_step(configuration, step, dry_run)
        except Exception as error:
            failed_steps += 1
            log(f"{step['app']}/qualityprofile: skipped after error: {error}")
    for step in HOST_LOGIN_PLAN:
        try:
            provision_host_login_step(configuration, step, dry_run)
        except Exception as error:
            failed_steps += 1
            log(f"{step['app']}/host-login: skipped after error: {error}")
    if failed_steps:
        log(
            f"WARNING: {failed_steps} of {total_steps} steps could not be applied; "
            "config was not fully reconciled this run"
        )
    return failed_steps
