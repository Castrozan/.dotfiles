import sys
from pathlib import Path

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import private_request_routing

FRIEND_PERMISSIONS = 160
ADMIN_PERMISSIONS = 2
MANAGE_REQUESTS_PERMISSIONS = 16


def test_an_ordinary_requester_gets_its_requests_overridden():
    assert private_request_routing.account_requests_can_be_overridden(
        FRIEND_PERMISSIONS
    )


def test_an_administrator_never_gets_its_requests_overridden():
    assert not private_request_routing.account_requests_can_be_overridden(
        ADMIN_PERMISSIONS
    )


def test_a_request_manager_never_gets_its_requests_overridden():
    assert not private_request_routing.account_requests_can_be_overridden(
        FRIEND_PERMISSIONS | MANAGE_REQUESTS_PERMISSIONS
    )


def test_default_service_index_is_the_array_position_not_the_server_id():
    servers = [
        {"id": 3, "isDefault": False, "is4k": False},
        {"id": 7, "isDefault": True, "is4k": False},
    ]

    assert private_request_routing.default_service_index(servers) == 1


def test_default_service_index_ignores_a_4k_default():
    servers = [{"id": 0, "isDefault": True, "is4k": True}]

    assert private_request_routing.default_service_index(servers) is None


def test_the_movie_rule_binds_to_radarr_only():
    movie_rule = private_request_routing.build_desired_override_rules(9, 0, 0)[0]

    assert movie_rule["rootFolder"] == private_request_routing.PRIVATE_MOVIE_ROOT_FOLDER
    assert movie_rule["radarrServiceId"] == 0
    assert movie_rule["sonarrServiceId"] is None
    assert movie_rule["users"] == "9"


def test_the_series_rules_bind_to_sonarr_only():
    series_rules = private_request_routing.build_desired_override_rules(9, 0, 0)[1:]

    for series_rule in series_rules:
        assert (
            series_rule["rootFolder"]
            == private_request_routing.PRIVATE_SERIES_ROOT_FOLDER
        )
        assert series_rule["sonarrServiceId"] == 0
        assert series_rule["radarrServiceId"] is None


def test_a_separate_series_rule_carries_the_anime_keyword():
    keywords = [
        rule["keywords"]
        for rule in private_request_routing.build_desired_override_rules(9, 0, 0)
    ]

    assert keywords == [None, None, private_request_routing.TMDB_ANIME_KEYWORD_ID]


def test_the_anime_and_ordinary_series_rules_occupy_different_slots():
    _, ordinary_series_rule, anime_series_rule = (
        private_request_routing.build_desired_override_rules(9, 0, 0)
    )

    assert private_request_routing.override_rule_slot(
        ordinary_series_rule
    ) != private_request_routing.override_rule_slot(anime_series_rule)


def test_only_private_root_folders_are_recognised_as_managed():
    assert private_request_routing.routes_to_a_private_root_folder(
        {"rootFolder": private_request_routing.PRIVATE_MOVIE_ROOT_FOLDER}
    )
    assert not private_request_routing.routes_to_a_private_root_folder(
        {"rootFolder": "/data/media/movies"}
    )


def test_a_rule_pointing_at_another_user_is_not_already_applied():
    desired_rule = private_request_routing.build_desired_override_rules(9, 0, 0)[0]
    stale_rule = {**desired_rule, "users": "4"}

    assert not private_request_routing.override_rule_already_applied(
        stale_rule, desired_rule
    )
    assert private_request_routing.override_rule_already_applied(
        {**desired_rule, "id": 1}, desired_rule
    )


def test_each_rule_describes_the_media_it_routes():
    descriptions = [
        private_request_routing.describe_override_rule(rule)
        for rule in private_request_routing.build_desired_override_rules(9, 0, 0)
    ]

    assert descriptions == [
        "movies to /data/media/movies-private",
        "series to /data/media/tv-private",
        "anime series to /data/media/tv-private",
    ]
