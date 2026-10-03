import runtime_credentials
import user_account_operations

JELLYFIN_ONLY_COMMANDS = {"sync"}


def build_jellyfin_context():
    return user_account_operations.ArrUsersContext(
        jellyfin_base_url=runtime_credentials.jellyfin_base_url(),
        jellyfin_api_key=runtime_credentials.read_jellyfin_api_key(),
    )


def build_context():
    return user_account_operations.ArrUsersContext(
        jellyfin_base_url=runtime_credentials.jellyfin_base_url(),
        jellyfin_api_key=runtime_credentials.read_jellyfin_api_key(),
        jellyseerr_base_url=runtime_credentials.jellyseerr_base_url(),
        jellyseerr_api_key=runtime_credentials.read_jellyseerr_api_key(),
    )


def build_context_for_command(command):
    if command in JELLYFIN_ONLY_COMMANDS:
        return build_jellyfin_context()
    return build_context()
