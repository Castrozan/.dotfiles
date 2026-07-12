import copy

from arr_api_client import create_resource, get_resource_list, update_resource
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


def apply_desired_profile_fields(body, desired, custom_formats):
    body["formatItems"] = build_format_items(
        custom_formats, desired.get("formatScores", {})
    )
    for field in OVERRIDABLE_PROFILE_FIELDS:
        if field in desired:
            body[field] = desired[field]
    return body


def create_quality_profile_from_template(
    base_url, api_key, desired, template, custom_formats, dry_run
):
    profile_name = desired["name"]
    template_name = desired["cloneFrom"]
    body = copy.deepcopy(template)
    body.pop("id", None)
    body["name"] = profile_name
    apply_desired_profile_fields(body, desired, custom_formats)
    if dry_run:
        log(
            f"[dry-run] qualityprofile '{profile_name}': would create from '{template_name}'"
        )
        return "would-create"
    create_resource(base_url, api_key, "qualityprofile", body)
    log(f"qualityprofile '{profile_name}': created from '{template_name}'")
    return "created"


def score_existing_quality_profile(
    base_url, api_key, desired, current_profile, custom_formats, dry_run
):
    profile_name = desired["name"]
    body = {**current_profile}
    apply_desired_profile_fields(body, desired, custom_formats)
    if dry_run:
        log(f"[dry-run] qualityprofile '{profile_name}': would set format scores")
        return "would-update"
    update_resource(base_url, api_key, "qualityprofile", current_profile["id"], body)
    log(f"qualityprofile '{profile_name}': scored")
    return "updated"


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
        unknown_formats = [
            name
            for name in desired.get("formatScores", {})
            if name not in known_format_names
        ]
        if unknown_formats:
            log(
                f"qualityprofile '{profile_name}': unknown custom formats {unknown_formats}"
            )
        current_profile = profiles_by_name.get(profile_name)
        if current_profile is not None:
            outcomes.append(
                score_existing_quality_profile(
                    base_url,
                    api_key,
                    desired,
                    current_profile,
                    custom_formats,
                    dry_run,
                )
            )
            continue
        template = profiles_by_name.get(desired.get("cloneFrom"))
        if template is None:
            log(
                f"qualityprofile '{profile_name}': absent and no template to clone, skipped"
            )
            outcomes.append("missing-profile")
            continue
        outcomes.append(
            create_quality_profile_from_template(
                base_url, api_key, desired, template, custom_formats, dry_run
            )
        )
    return outcomes
