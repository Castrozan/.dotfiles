import sys
from pathlib import Path

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import friend_account_policy
import jellyseerr_account_permissions
import private_request_routing

OWNER_ACCOUNT = {"id": 1, "jellyfinUsername": "jellyseerr", "permissions": 2}
DAILY_DRIVER_ACCOUNT = {"id": 2, "jellyfinUsername": "owner", "permissions": 2}
FRIEND_ACCOUNT = {"id": 4, "jellyfinUsername": "Friend", "permissions": 160}
ROUTED_ACCOUNT = {
    "id": 9,
    "jellyfinUsername": private_request_routing.PRIVATE_REQUEST_ACCOUNT_USERNAME,
    "permissions": 160,
}


def test_the_declared_permissions_never_suppress_the_private_request_routing():
    assert (
        jellyseerr_account_permissions.SELF_APPROVING_REQUESTER_PERMISSIONS
        & private_request_routing.OVERRIDE_SUPPRESSING_PERMISSIONS
        == 0
    )


def test_the_declared_permissions_still_request_and_auto_approve():
    assert (
        jellyseerr_account_permissions.SELF_APPROVING_REQUESTER_PERMISSIONS
        & friend_account_policy.JELLYSEERR_PERMISSION_REQUEST
    )
    assert (
        jellyseerr_account_permissions.SELF_APPROVING_REQUESTER_PERMISSIONS
        & friend_account_policy.JELLYSEERR_PERMISSION_AUTO_APPROVE
    )


def test_a_friend_already_holds_the_declared_permissions():
    assert (
        jellyseerr_account_permissions.accounts_needing_permission_rewrite(
            [FRIEND_ACCOUNT, ROUTED_ACCOUNT]
        )
        == []
    )


def test_the_owner_account_administers_whatever_its_permissions_say():
    assert jellyseerr_account_permissions.account_administers_jellyseerr(
        {"id": 1, "jellyfinUsername": "renamed", "permissions": 160}
    )


def test_a_declared_administrator_username_administers_at_any_id():
    assert jellyseerr_account_permissions.account_administers_jellyseerr(
        {"id": 12, "jellyfinUsername": "jellyseerr", "permissions": 160}
    )


def test_an_undeclared_administrator_is_rewritten_back_to_requesting():
    rewritten = jellyseerr_account_permissions.accounts_needing_permission_rewrite(
        [OWNER_ACCOUNT, DAILY_DRIVER_ACCOUNT, FRIEND_ACCOUNT]
    )

    assert [account["id"] for account in rewritten] == [DAILY_DRIVER_ACCOUNT["id"]]


def test_the_administrator_is_never_offered_for_rewrite():
    rewritten = jellyseerr_account_permissions.accounts_needing_permission_rewrite(
        [OWNER_ACCOUNT, DAILY_DRIVER_ACCOUNT]
    )

    assert OWNER_ACCOUNT not in rewritten


def test_an_account_is_named_by_its_jellyfin_username():
    assert (
        jellyseerr_account_permissions.describe_account(DAILY_DRIVER_ACCOUNT) == "owner"
    )


def test_an_account_without_any_name_is_still_describable():
    assert "7" in jellyseerr_account_permissions.describe_account({"id": 7})


def test_a_null_display_name_never_becomes_an_account_name():
    assert jellyseerr_account_permissions.resolve_account_names(
        {"id": 3, "displayName": None, "jellyfinUsername": "joshen", "username": None}
    ) == {"joshen"}
