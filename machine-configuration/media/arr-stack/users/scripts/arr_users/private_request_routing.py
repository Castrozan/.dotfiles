PRIVATE_REQUEST_ACCOUNT_USERNAME = "private-requests"

PRIVATE_MOVIE_ROOT_FOLDER = "/data/media/movies-private"
PRIVATE_SERIES_ROOT_FOLDER = "/data/media/tv-private"
PRIVATE_ROOT_FOLDERS = frozenset(
    {PRIVATE_MOVIE_ROOT_FOLDER, PRIVATE_SERIES_ROOT_FOLDER}
)

TMDB_ANIME_KEYWORD_ID = "210024"

JELLYSEERR_PERMISSION_ADMIN = 2
JELLYSEERR_PERMISSION_MANAGE_REQUESTS = 16
OVERRIDE_SUPPRESSING_PERMISSIONS = (
    JELLYSEERR_PERMISSION_ADMIN | JELLYSEERR_PERMISSION_MANAGE_REQUESTS
)

OVERRIDE_RULE_FIELDS = (
    "users",
    "genre",
    "language",
    "keywords",
    "profileId",
    "rootFolder",
    "tags",
    "radarrServiceId",
    "sonarrServiceId",
)


def account_requests_can_be_overridden(jellyseerr_permissions):
    return not int(jellyseerr_permissions or 0) & OVERRIDE_SUPPRESSING_PERMISSIONS


def default_service_index(jellyseerr_service_servers):
    for index, server in enumerate(jellyseerr_service_servers):
        if server.get("isDefault") and not server.get("is4k"):
            return index
    return None


def build_override_rule(
    routed_users,
    root_folder,
    radarr_service_id=None,
    sonarr_service_id=None,
    keywords=None,
):
    return {
        "users": routed_users,
        "genre": None,
        "language": None,
        "keywords": keywords,
        "profileId": None,
        "rootFolder": root_folder,
        "tags": None,
        "radarrServiceId": radarr_service_id,
        "sonarrServiceId": sonarr_service_id,
    }


def build_desired_override_rules(
    jellyseerr_user_id, radarr_service_index, sonarr_service_index
):
    routed_users = str(jellyseerr_user_id)
    return [
        build_override_rule(
            routed_users,
            PRIVATE_MOVIE_ROOT_FOLDER,
            radarr_service_id=radarr_service_index,
        ),
        build_override_rule(
            routed_users,
            PRIVATE_SERIES_ROOT_FOLDER,
            sonarr_service_id=sonarr_service_index,
        ),
        build_override_rule(
            routed_users,
            PRIVATE_SERIES_ROOT_FOLDER,
            sonarr_service_id=sonarr_service_index,
            keywords=TMDB_ANIME_KEYWORD_ID,
        ),
    ]


def override_rule_slot(override_rule):
    return (
        override_rule.get("rootFolder"),
        override_rule.get("radarrServiceId"),
        override_rule.get("sonarrServiceId"),
        override_rule.get("keywords"),
    )


def routes_to_a_private_root_folder(override_rule):
    return override_rule.get("rootFolder") in PRIVATE_ROOT_FOLDERS


def override_rule_already_applied(existing_override_rule, desired_override_rule):
    return all(
        existing_override_rule.get(field) == desired_override_rule.get(field)
        for field in OVERRIDE_RULE_FIELDS
    )


def describe_override_rule(override_rule):
    if override_rule.get("radarrServiceId") is not None:
        requested_kind = "movies"
    elif override_rule.get("keywords") == TMDB_ANIME_KEYWORD_ID:
        requested_kind = "anime series"
    else:
        requested_kind = "series"
    return f"{requested_kind} to {override_rule.get('rootFolder')}"
