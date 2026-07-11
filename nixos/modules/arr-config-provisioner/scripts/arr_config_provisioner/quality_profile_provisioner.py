from arr_api_client import get_resource_list, update_resource
from provisioner_logging import log

OVERRIDABLE_PROFILE_FIELDS = (
    "upgradeAllowed",
    "minFormatScore",
    "cutoffFormatScore",
)


def build_format_items(custom_formats, format_scores):
    return [
        {
            "format": custom_format["id"],
            "name": custom_format["name"],
            "score": format_scores.get(custom_format["name"], 0),
        }
        for custom_format in custom_formats
    ]


def provision_quality_profiles(base_url, api_key, desired_profiles, dry_run):
    custom_formats = get_resource_list(base_url, api_key, "customformat")
    known_format_names = {custom_format["name"] for custom_format in custom_formats}
    profiles_by_name = {
        profile["name"]: profile
        for profile in get_resource_list(base_url, api_key, "qualityprofile")
    }
    outcomes = []
    for desired in desired_profiles:
        profile_name = desired["name"]
        current_profile = profiles_by_name.get(profile_name)
        if current_profile is None:
            log(f"qualityprofile '{profile_name}': absent, cannot score")
            outcomes.append("missing-profile")
            continue
        format_scores = desired.get("formatScores", {})
        unknown_formats = [
            name for name in format_scores if name not in known_format_names
        ]
        if unknown_formats:
            log(
                f"qualityprofile '{profile_name}': unknown custom formats {unknown_formats}"
            )
        body = {**current_profile}
        body["formatItems"] = build_format_items(custom_formats, format_scores)
        for field in OVERRIDABLE_PROFILE_FIELDS:
            if field in desired:
                body[field] = desired[field]
        if dry_run:
            log(f"[dry-run] qualityprofile '{profile_name}': would set format scores")
            outcomes.append("would-update")
            continue
        update_resource(
            base_url, api_key, "qualityprofile", current_profile["id"], body
        )
        log(f"qualityprofile '{profile_name}': scored")
        outcomes.append("updated")
    return outcomes
