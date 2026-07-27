import sys
from pathlib import Path

import pytest
from arr_users_test_doubles import make_context

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import private_request_routing
import request_routing_synchronization

ROUTED_ACCOUNT = {
    "id": 9,
    "displayName": private_request_routing.PRIVATE_REQUEST_ACCOUNT_USERNAME,
    "permissions": 160,
}
FRIEND_ACCOUNT = {"id": 4, "displayName": "Rogerio", "permissions": 160}
DEFAULT_SERVERS = [{"id": 0, "isDefault": True, "is4k": False}]
PUBLIC_RULE = {"id": 50, "rootFolder": "/data/media/movies", "users": "4"}


def stub_jellyseerr(monkeypatch, users, override_rules=(), servers=DEFAULT_SERVERS):
    calls = {"created": [], "updated": [], "deleted": []}
    monkeypatch.setattr(
        request_routing_synchronization.jellyseerr_api_client,
        "list_users",
        lambda base_url, api_key: list(users),
    )
    monkeypatch.setattr(
        request_routing_synchronization.jellyseerr_api_client,
        "list_service_servers",
        lambda base_url, api_key, service_name: list(servers),
    )
    monkeypatch.setattr(
        request_routing_synchronization.jellyseerr_api_client,
        "list_override_rules",
        lambda base_url, api_key: list(override_rules),
    )
    monkeypatch.setattr(
        request_routing_synchronization.jellyseerr_api_client,
        "create_override_rule",
        lambda base_url, api_key, rule: calls["created"].append(rule),
    )
    monkeypatch.setattr(
        request_routing_synchronization.jellyseerr_api_client,
        "update_override_rule",
        lambda base_url, api_key, rule_id, rule: calls["updated"].append(
            (rule_id, rule)
        ),
    )
    monkeypatch.setattr(
        request_routing_synchronization.jellyseerr_api_client,
        "delete_override_rule",
        lambda base_url, api_key, rule_id: calls["deleted"].append(rule_id),
    )
    return calls


def test_every_declared_rule_is_created_when_none_exist(monkeypatch):
    calls = stub_jellyseerr(monkeypatch, [FRIEND_ACCOUNT, ROUTED_ACCOUNT])

    result = request_routing_synchronization.synchronize_request_routing(make_context())

    assert [rule["rootFolder"] for rule in calls["created"]] == [
        private_request_routing.PRIVATE_MOVIE_ROOT_FOLDER,
        private_request_routing.PRIVATE_SERIES_ROOT_FOLDER,
        private_request_routing.PRIVATE_SERIES_ROOT_FOLDER,
    ]
    assert all(rule["users"] == "9" for rule in calls["created"])
    assert result["routed_account"] == (
        private_request_routing.PRIVATE_REQUEST_ACCOUNT_USERNAME
    )


def test_nothing_is_written_when_the_routing_account_does_not_exist(monkeypatch):
    calls = stub_jellyseerr(monkeypatch, [FRIEND_ACCOUNT])

    result = request_routing_synchronization.synchronize_request_routing(make_context())

    assert calls == {"created": [], "updated": [], "deleted": []}
    assert result["routed_account"] is None


def test_an_admin_routing_account_is_refused_rather_than_silently_unrouted(monkeypatch):
    calls = stub_jellyseerr(monkeypatch, [{**ROUTED_ACCOUNT, "permissions": 2}])

    with pytest.raises(ValueError, match="skip every override rule"):
        request_routing_synchronization.synchronize_request_routing(make_context())

    assert calls["created"] == []


def test_a_missing_default_server_is_refused(monkeypatch):
    calls = stub_jellyseerr(monkeypatch, [ROUTED_ACCOUNT], servers=[])

    with pytest.raises(ValueError, match="no default"):
        request_routing_synchronization.synchronize_request_routing(make_context())

    assert calls["created"] == []


def test_a_rule_left_pointing_at_the_wrong_account_is_rewritten(monkeypatch):
    stale_rule = {
        **private_request_routing.build_desired_override_rules(4, 0, 0)[0],
        "id": 11,
    }
    calls = stub_jellyseerr(monkeypatch, [ROUTED_ACCOUNT], override_rules=[stale_rule])

    result = request_routing_synchronization.synchronize_request_routing(make_context())

    assert calls["updated"][0][0] == 11
    assert calls["updated"][0][1]["users"] == "9"
    assert result["updated_rules"] == ["movies to /data/media/movies-private"]
    assert len(calls["created"]) == 2


def test_an_already_applied_rule_is_left_untouched(monkeypatch):
    applied_rules = [
        {**rule, "id": index}
        for index, rule in enumerate(
            private_request_routing.build_desired_override_rules(9, 0, 0)
        )
    ]
    calls = stub_jellyseerr(monkeypatch, [ROUTED_ACCOUNT], override_rules=applied_rules)

    request_routing_synchronization.synchronize_request_routing(make_context())

    assert calls == {"created": [], "updated": [], "deleted": []}


def test_a_private_rule_no_longer_declared_is_removed(monkeypatch):
    orphan_rule = {
        **private_request_routing.build_override_rule(
            "9", private_request_routing.PRIVATE_MOVIE_ROOT_FOLDER, radarr_service_id=4
        ),
        "id": 77,
    }
    calls = stub_jellyseerr(monkeypatch, [ROUTED_ACCOUNT], override_rules=[orphan_rule])

    result = request_routing_synchronization.synchronize_request_routing(make_context())

    assert calls["deleted"] == [77]
    assert result["removed_rules"] == ["movies to /data/media/movies-private"]


def test_a_rule_routing_to_a_public_root_folder_is_never_touched(monkeypatch):
    calls = stub_jellyseerr(monkeypatch, [ROUTED_ACCOUNT], override_rules=[PUBLIC_RULE])

    request_routing_synchronization.synchronize_request_routing(make_context())

    assert calls["deleted"] == []
    assert calls["updated"] == []
    assert len(calls["created"]) == 3
