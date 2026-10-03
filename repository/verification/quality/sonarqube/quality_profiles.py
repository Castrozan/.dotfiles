from sonar_api import request


def _collect_rules(profile, inheritance):
    actual_rules = {}
    page = 1
    while True:
        response = request(
            "get",
            "/api/rules/search",
            qprofile=profile["key"],
            activation="true",
            inheritance=inheritance,
            ps=500,
            p=page,
        )
        actual_rules.update({rule["key"]: inheritance for rule in response["rules"]})
        if page * 500 >= response["total"]:
            return actual_rules
        page += 1


def remove_undeclared_rules(profile, desired_rules):
    configured_rule_keys = {rule["key"] for rule in desired_rules}
    actual_rules = {}
    for inheritance in ("NONE", "OVERRIDES"):
        actual_rules.update(_collect_rules(profile, inheritance))
    for key in sorted(actual_rules.keys() - configured_rule_keys):
        if actual_rules[key] == "OVERRIDES":
            request(
                "post",
                "/api/qualityprofiles/activate_rule",
                key=profile["key"],
                rule=key,
                reset="true",
            )
        else:
            request(
                "post",
                "/api/qualityprofiles/deactivate_rule",
                key=profile["key"],
                rule=key,
            )


def _find_or_create_profile(organization, desired, profiles):
    profile = next(
        (profile for profile in profiles if profile["name"] == desired["name"]),
        None,
    )
    if profile is None:
        return request(
            "post",
            "/api/qualityprofiles/create",
            organization=organization,
            language=desired["language"],
            name=desired["name"],
        )["profile"]
    return profile


def configure_quality_profiles(configuration):
    organization = configuration["organization"]
    for desired in configuration["qualityProfiles"]:
        profiles = request(
            "get",
            "/api/qualityprofiles/search",
            organization=organization,
            language=desired["language"],
        )["profiles"]
        profile = _find_or_create_profile(organization, desired, profiles)
        parent = next(
            profile for profile in profiles if profile["name"] == desired["parent"]
        )
        if profile.get("parentKey") != parent["key"]:
            request(
                "post",
                "/api/qualityprofiles/change_parent",
                key=profile["key"],
                parentKey=parent["key"],
            )
        remove_undeclared_rules(profile, desired["rules"])
        for rule in desired["rules"]:
            request(
                "post",
                "/api/qualityprofiles/activate_rule",
                key=profile["key"],
                rule=rule["key"],
                params=";".join(
                    f"{key}={value}" for key, value in rule["parameters"].items()
                ),
            )
        request(
            "post",
            "/api/qualityprofiles/add_project",
            project=configuration["project"],
            key=profile["key"],
        )
