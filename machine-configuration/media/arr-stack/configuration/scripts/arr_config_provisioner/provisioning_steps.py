from arr_api_client import wait_for_api_ready
from host_auth_provisioner import provision_host_login
from jellyseerr_sonarr_profile_provisioner import provision_sonarr_profiles
from provisioner_logging import log
from qbittorrent_preference_provisioner import provision_qbittorrent_preferences
from quality_profile_provisioner import provision_quality_profiles
from runtime_config import (
    load_desired_objects,
    load_optional_desired_objects,
    read_app_api_key,
)
from upsert_engine import upsert_resource

APP_API_VERSION = {"radarr": "v3", "sonarr": "v3", "prowlarr": "v1"}


def build_base_url(bind_address, port, app):
    return f"http://{bind_address}:{port}/api/{APP_API_VERSION[app]}"


def open_ready_app(configuration, step):
    app = step["app"]
    base_url = build_base_url(configuration["bind_address"], step["port"], app)
    api_key = read_app_api_key(configuration["config_root"], app)
    if not wait_for_api_ready(base_url, api_key):
        raise RuntimeError(f"{app} api not reachable")
    return base_url, api_key


def provision_step(configuration, step, dry_run):
    base_url, api_key = open_ready_app(configuration, step)
    desired_objects = load_desired_objects(
        configuration["desired_state_dir"],
        step["app"],
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
    log(f"{step['app']}/{step['resource']}: {outcomes}")


def provision_quality_profile_step(configuration, step, dry_run):
    base_url, api_key = open_ready_app(configuration, step)
    desired_profiles = load_optional_desired_objects(
        configuration["desired_state_dir"],
        step["app"],
        "qualityprofile",
        configuration["secret_map"],
    )
    if not desired_profiles:
        return
    outcomes = provision_quality_profiles(base_url, api_key, desired_profiles, dry_run)
    log(f"{step['app']}/qualityprofile: {outcomes}")


def provision_jellyseerr_sonarr_profile_step(configuration, step, dry_run):
    base_url, api_key = open_ready_app(configuration, step)
    jellyseerr_api_key = configuration["jellyseerr_api_key"]
    if not jellyseerr_api_key:
        raise RuntimeError("jellyseerr api key unavailable")
    desired_routes = load_optional_desired_objects(
        configuration["desired_state_dir"],
        "jellyseerr",
        "sonarr",
        configuration["secret_map"],
    )
    if not desired_routes:
        return
    outcomes = provision_sonarr_profiles(
        configuration["jellyseerr_base_url"],
        jellyseerr_api_key,
        base_url,
        api_key,
        desired_routes,
        dry_run,
    )
    log(f"jellyseerr/sonarr: {outcomes}")


def provision_host_login_step(configuration, step, dry_run):
    base_url, api_key = open_ready_app(configuration, step)
    outcome = provision_host_login(
        base_url,
        api_key,
        configuration["login_username"],
        configuration["login_passwords"].get(step["app"], ""),
        dry_run,
    )
    log(f"{step['app']}/host-login: {outcome}")


def provision_qbittorrent_preference_step(configuration, step, dry_run):
    desired_preferences = load_optional_desired_objects(
        configuration["desired_state_dir"],
        step["app"],
        "preferences",
        configuration["secret_map"],
    )
    outcome = provision_qbittorrent_preferences(
        f"http://{configuration['bind_address']}:{step['port']}",
        configuration["qbittorrent_username"],
        configuration["qbittorrent_password"],
        desired_preferences,
        dry_run,
    )
    log(f"{step['app']}/preferences: {outcome}")
