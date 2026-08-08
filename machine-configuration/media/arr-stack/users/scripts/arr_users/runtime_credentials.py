import json
import os
import sys
from pathlib import Path

DEFAULT_JELLYFIN_BASE_URL = "http://127.0.0.1:8096"
DEFAULT_JELLYSEERR_BASE_URL = "http://127.0.0.1:5055"
DEFAULT_KAVITA_BASE_URL = "http://127.0.0.1:5000"
DEFAULT_JELLYFIN_API_KEY_FILE = "/run/agenix/jellyfin-admin-api-key"
DEFAULT_KAVITA_API_KEY_FILE = "/run/agenix/kavita-admin-api-key"
DEFAULT_JELLYSEERR_SETTINGS_FILE = str(
    Path.home() / "arr-stack" / "config" / "jellyseerr" / "settings.json"
)


def jellyfin_base_url() -> str:
    return os.environ.get("ARR_USERS_JELLYFIN_BASE_URL", DEFAULT_JELLYFIN_BASE_URL)


def jellyseerr_base_url() -> str:
    return os.environ.get("ARR_USERS_JELLYSEERR_BASE_URL", DEFAULT_JELLYSEERR_BASE_URL)


def kavita_base_url() -> str:
    return os.environ.get("ARR_USERS_KAVITA_BASE_URL", DEFAULT_KAVITA_BASE_URL)


def read_declared_string_list(environment_variable_name: str) -> list:
    declared_value = os.environ.get(environment_variable_name, "").strip()
    if not declared_value:
        return []
    return [entry for entry in json.loads(declared_value) if entry]


def kavita_public_library_names() -> list:
    return read_declared_string_list("ARR_USERS_KAVITA_PUBLIC_LIBRARIES")


def kavita_privileged_account_usernames() -> list:
    return read_declared_string_list("ARR_USERS_KAVITA_PRIVILEGED_ACCOUNTS")


def kavita_friend_account_usernames() -> list:
    return read_declared_string_list("ARR_USERS_KAVITA_FRIEND_ACCOUNTS")


def kavita_source_folder_library_name() -> str:
    return os.environ.get("ARR_USERS_KAVITA_SOURCE_FOLDER_LIBRARY", "")


def kavita_source_root_host_path() -> str:
    return os.environ.get("ARR_USERS_KAVITA_SOURCE_ROOT_HOST_PATH", "")


def kavita_source_root_container_path() -> str:
    return os.environ.get("ARR_USERS_KAVITA_SOURCE_ROOT_CONTAINER_PATH", "")


def read_required_secret_file(secret_file_path: Path, description: str) -> str:
    if not secret_file_path.is_file():
        print(f"{description} not found at {secret_file_path}", file=sys.stderr)
        raise SystemExit(1)
    secret_value = secret_file_path.read_text(encoding="utf-8").strip()
    if not secret_value:
        print(f"{description} at {secret_file_path} is empty", file=sys.stderr)
        raise SystemExit(1)
    return secret_value


def read_jellyfin_api_key() -> str:
    secret_file_path = Path(
        os.environ.get("ARR_USERS_JELLYFIN_API_KEY_FILE", DEFAULT_JELLYFIN_API_KEY_FILE)
    )
    return read_required_secret_file(secret_file_path, "Jellyfin admin API key")


def read_kavita_api_key() -> str:
    secret_file_path = Path(
        os.environ.get("ARR_USERS_KAVITA_API_KEY_FILE", DEFAULT_KAVITA_API_KEY_FILE)
    )
    return read_required_secret_file(secret_file_path, "Kavita admin API key")


def read_jellyseerr_api_key() -> str:
    settings_file_path = Path(
        os.environ.get(
            "ARR_USERS_JELLYSEERR_SETTINGS_FILE", DEFAULT_JELLYSEERR_SETTINGS_FILE
        )
    )
    if not settings_file_path.is_file():
        print(f"Jellyseerr settings not found at {settings_file_path}", file=sys.stderr)
        raise SystemExit(1)
    settings = json.loads(settings_file_path.read_text(encoding="utf-8"))
    api_key = settings.get("main", {}).get("apiKey", "")
    if not api_key:
        print(f"Jellyseerr apiKey missing from {settings_file_path}", file=sys.stderr)
        raise SystemExit(1)
    return api_key
