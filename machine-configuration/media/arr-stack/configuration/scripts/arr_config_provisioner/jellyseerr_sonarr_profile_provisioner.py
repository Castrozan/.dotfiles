from arr_api_client import get_resource_list, request_json
from provisioner_logging import log

MANAGED_SETTINGS_FIELDS = (
    "activeProfileId",
    "activeProfileName",
    "activeAnimeProfileId",
    "activeAnimeProfileName",
    "activeAnimeDirectory",
)


def build_desired_server_settings(current_server, desired_route, profiles_by_name):
    standard_profile_name = desired_route["standardProfileName"]
    anime_profile_name = desired_route["animeProfileName"]
    standard_profile = profiles_by_name.get(standard_profile_name)
    anime_profile = profiles_by_name.get(anime_profile_name)
    if standard_profile is None or anime_profile is None:
        return None
    return {
        **current_server,
        "activeProfileId": standard_profile["id"],
        "activeProfileName": standard_profile_name,
        "activeAnimeProfileId": anime_profile["id"],
        "activeAnimeProfileName": anime_profile_name,
        "activeAnimeDirectory": desired_route.get(
            "animeDirectory", current_server.get("activeDirectory")
        ),
    }


def managed_settings_match(current_server, desired_server):
    return all(
        current_server.get(field) == desired_server.get(field)
        for field in MANAGED_SETTINGS_FIELDS
    )


def provision_sonarr_profiles(
    jellyseerr_base_url,
    jellyseerr_api_key,
    sonarr_base_url,
    sonarr_api_key,
    desired_routes,
    dry_run,
):
    current_servers = (
        request_json(
            "GET",
            f"{jellyseerr_base_url}/api/v1/settings/sonarr",
            jellyseerr_api_key,
        )
        or []
    )
    profiles_by_name = {
        profile["name"]: profile
        for profile in get_resource_list(
            sonarr_base_url, sonarr_api_key, "qualityprofile"
        )
    }
    outcomes = []
    for desired_route in desired_routes:
        server_name = desired_route["name"]
        current_server = next(
            (server for server in current_servers if server.get("name") == server_name),
            None,
        )
        if current_server is None:
            log(f"jellyseerr/sonarr '{server_name}': server absent")
            outcomes.append("missing-server")
            continue
        desired_server = build_desired_server_settings(
            current_server, desired_route, profiles_by_name
        )
        if desired_server is None:
            log(f"jellyseerr/sonarr '{server_name}': profile absent")
            outcomes.append("missing-profile")
            continue
        if managed_settings_match(current_server, desired_server):
            outcomes.append("unchanged")
            continue
        if dry_run:
            log(f"[dry-run] jellyseerr/sonarr '{server_name}': would update")
            outcomes.append("would-update")
            continue
        request_json(
            "PUT",
            f"{jellyseerr_base_url}/api/v1/settings/sonarr/{current_server['id']}",
            jellyseerr_api_key,
            desired_server,
        )
        outcomes.append("updated")
    return outcomes
