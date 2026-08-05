import sys
from pathlib import Path

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import friend_account_policy

PUBLIC_LIBRARY_IDS = ["movies-id", "tv-id"]


def test_build_friend_policy_forces_non_administrator():
    policy = friend_account_policy.build_friend_policy(
        {"IsAdministrator": True}, PUBLIC_LIBRARY_IDS
    )
    assert policy["IsAdministrator"] is False


def test_build_friend_policy_denies_content_deletion_and_live_tv():
    policy = friend_account_policy.build_friend_policy(
        {"EnableContentDeletion": True, "EnableLiveTvAccess": True}, PUBLIC_LIBRARY_IDS
    )
    assert policy["EnableContentDeletion"] is False
    assert policy["EnableLiveTvAccess"] is False


def test_build_friend_policy_preserves_unrelated_keys():
    policy = friend_account_policy.build_friend_policy(
        {"AuthenticationProviderId": "provider", "MaxActiveSessions": 3},
        PUBLIC_LIBRARY_IDS,
    )
    assert policy["AuthenticationProviderId"] == "provider"
    assert policy["MaxActiveSessions"] == 3


def test_build_friend_policy_does_not_mutate_input():
    original_policy = {"IsAdministrator": True}
    friend_account_policy.build_friend_policy(original_policy, PUBLIC_LIBRARY_IDS)
    assert original_policy["IsAdministrator"] is True


def test_build_friend_policy_restricts_visibility_to_public_libraries():
    policy = friend_account_policy.build_friend_policy(
        {"EnableAllFolders": True, "EnabledFolders": []}, PUBLIC_LIBRARY_IDS
    )
    assert policy["EnableAllFolders"] is False
    assert policy["EnabledFolders"] == PUBLIC_LIBRARY_IDS


def test_friend_policy_overrides_never_grant_every_folder():
    assert "EnableAllFolders" not in friend_account_policy.FRIEND_POLICY_OVERRIDES


def test_build_library_visibility_policy_preserves_disabled_accounts():
    policy = friend_account_policy.build_library_visibility_policy(
        {"IsDisabled": True, "EnableAllFolders": True}, PUBLIC_LIBRARY_IDS
    )
    assert policy["IsDisabled"] is True
    assert policy["EnableAllFolders"] is False
    assert policy["EnabledFolders"] == PUBLIC_LIBRARY_IDS


def test_build_library_visibility_policy_does_not_mutate_input():
    original_policy = {"EnableAllFolders": True}
    friend_account_policy.build_library_visibility_policy(
        original_policy, PUBLIC_LIBRARY_IDS
    )
    assert original_policy["EnableAllFolders"] is True


def test_build_enabled_state_policy_toggles_is_disabled():
    assert friend_account_policy.build_enabled_state_policy({}, False)["IsDisabled"]
    assert not friend_account_policy.build_enabled_state_policy({}, True)["IsDisabled"]


def test_is_administrator_reads_nested_policy():
    assert friend_account_policy.is_administrator({"Policy": {"IsAdministrator": True}})
    assert not friend_account_policy.is_administrator({"Policy": {}})
    assert not friend_account_policy.is_administrator({})


def test_friend_jellyseerr_permissions_combine_request_and_auto_approve():
    assert friend_account_policy.FRIEND_JELLYSEERR_PERMISSIONS_BITMASK == 160
    assert (
        friend_account_policy.FRIEND_JELLYSEERR_PERMISSIONS_BITMASK
        == friend_account_policy.JELLYSEERR_PERMISSION_REQUEST
        | friend_account_policy.JELLYSEERR_PERMISSION_AUTO_APPROVE
    )
