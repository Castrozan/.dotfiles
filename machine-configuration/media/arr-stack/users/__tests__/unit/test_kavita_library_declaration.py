import json
import sys
from pathlib import Path

import pytest

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import kavita_account_policy
import kavita_library_declaration

KAVITA_LIBRARIES = [
    {"id": 1, "name": "Manga", "folders": ["/manga"]},
    {"id": 2, "name": "Manga (Private)", "folders": ["/manga-private"]},
]


def declare(monkeypatch, public_libraries, privileged_accounts, friend_accounts=()):
    monkeypatch.setenv(
        "ARR_USERS_KAVITA_PUBLIC_LIBRARIES", json.dumps(list(public_libraries))
    )
    monkeypatch.setenv(
        "ARR_USERS_KAVITA_PRIVILEGED_ACCOUNTS", json.dumps(list(privileged_accounts))
    )
    monkeypatch.setenv(
        "ARR_USERS_KAVITA_FRIEND_ACCOUNTS", json.dumps(list(friend_accounts))
    )


def test_a_friend_is_pinned_to_the_declared_public_libraries(monkeypatch):
    declare(monkeypatch, ["Manga"], ["zanoni"])

    assert kavita_library_declaration.resolve_visible_library_ids(
        KAVITA_LIBRARIES, "Xamitos"
    ) == [1]


def test_an_undeclared_registration_is_pinned_to_the_public_libraries(monkeypatch):
    declare(monkeypatch, ["Manga"], ["zanoni"], ["Xamitos"])

    assert kavita_library_declaration.resolve_visible_library_ids(
        KAVITA_LIBRARIES, "someone-who-just-registered"
    ) == [1]


def test_a_privileged_account_reaches_every_library(monkeypatch):
    declare(monkeypatch, ["Manga"], ["zanoni"])

    assert kavita_library_declaration.resolve_visible_library_ids(
        KAVITA_LIBRARIES, "zanoni"
    ) == [1, 2]


def test_privilege_is_matched_without_regard_to_case(monkeypatch):
    declare(monkeypatch, ["Manga"], ["Zanoni"])

    assert kavita_library_declaration.account_sees_every_library("zanoni")


def test_a_missing_declared_public_library_refuses_the_write(monkeypatch):
    declare(monkeypatch, ["Manga", "Light Novels"], ["zanoni"])

    with pytest.raises(ValueError) as error_info:
        kavita_library_declaration.resolve_public_library_ids(KAVITA_LIBRARIES)
    assert "Light Novels" in str(error_info.value)


def test_an_undeclared_library_counts_as_withheld(monkeypatch):
    declare(monkeypatch, ["Manga"], ["zanoni"])

    assert kavita_library_declaration.private_library_names_present(
        KAVITA_LIBRARIES
    ) == ["Manga (Private)"]


def test_an_undeclared_account_is_reported(monkeypatch):
    declare(monkeypatch, ["Manga"], ["zanoni"], ["Xamitos"])

    assert kavita_library_declaration.undeclared_account_usernames(
        [{"username": "zanoni"}, {"username": "Xamitos"}, {"username": "stranger"}]
    ) == ["stranger"]


def test_an_empty_declaration_grants_a_friend_nothing(monkeypatch):
    declare(monkeypatch, [], ["zanoni"])

    assert (
        kavita_library_declaration.resolve_visible_library_ids(
            KAVITA_LIBRARIES, "Xamitos"
        )
        == []
    )


def test_a_friend_loses_every_privileged_role():
    account_update = kavita_account_policy.build_account_library_access_update(
        {
            "id": 4,
            "username": "Xamitos",
            "roles": ["Admin", "Login", "Download", "Promote", "ChangeRestriction"],
            "ageRestriction": {"ageRating": 0, "includeUnknowns": True},
        },
        [1],
        False,
    )

    assert account_update["roles"] == ["Login", "Download"]
    assert account_update["libraries"] == [1]


def test_a_privileged_account_keeps_its_roles():
    account_update = kavita_account_policy.build_account_library_access_update(
        {"id": 1, "username": "zanoni", "roles": ["Admin", "Login"]}, [1, 2], True
    )

    assert account_update["roles"] == ["Admin", "Login"]
    assert account_update["libraries"] == [1, 2]


def test_an_account_without_an_age_restriction_still_gets_one():
    account_update = kavita_account_policy.build_account_library_access_update(
        {"id": 5, "username": "new", "roles": ["Login"]}, [1], False
    )

    assert account_update["ageRestriction"] == (
        kavita_account_policy.UNRESTRICTED_AGE_RESTRICTION
    )
