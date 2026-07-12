FRIEND_POLICY_OVERRIDES = {
    "IsAdministrator": False,
    "IsDisabled": False,
    "IsHidden": True,
    "EnableRemoteAccess": True,
    "EnableMediaPlayback": True,
    "EnableAllFolders": True,
    "EnableAllDevices": True,
    "EnableContentDeletion": False,
    "EnableContentDownloading": True,
    "EnableUserPreferenceAccess": True,
    "EnableLiveTvAccess": False,
    "EnableSyncTranscoding": True,
}

JELLYSEERR_PERMISSION_REQUEST = 32
JELLYSEERR_PERMISSION_AUTO_APPROVE = 128
FRIEND_JELLYSEERR_PERMISSIONS_BITMASK = (
    JELLYSEERR_PERMISSION_REQUEST | JELLYSEERR_PERMISSION_AUTO_APPROVE
)


def build_friend_policy(current_policy):
    friend_policy = dict(current_policy)
    friend_policy.update(FRIEND_POLICY_OVERRIDES)
    return friend_policy


def build_enabled_state_policy(current_policy, enabled):
    updated_policy = dict(current_policy)
    updated_policy["IsDisabled"] = not enabled
    return updated_policy


def is_administrator(jellyfin_user):
    return bool(jellyfin_user.get("Policy", {}).get("IsAdministrator"))
