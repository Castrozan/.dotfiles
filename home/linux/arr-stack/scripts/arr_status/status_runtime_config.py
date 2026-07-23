import json
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_STACK_HOME_DIRECTORY = str(Path.home() / "arr-stack")
DEFAULT_JELLYSEERR_BASE_URL = "http://127.0.0.1:5055"
RADARR_PORT = 7878
SONARR_PORT = 8989


@dataclass
class ArrEndpoint:
    base_url: str
    api_key: str


def stack_home_directory() -> Path:
    return Path(os.environ.get("ARR_STATUS_STACK_HOME", DEFAULT_STACK_HOME_DIRECTORY))


def jellyseerr_base_url() -> str:
    return os.environ.get("ARR_STATUS_JELLYSEERR_BASE_URL", DEFAULT_JELLYSEERR_BASE_URL)


def jellyseerr_settings_file() -> Path:
    override = os.environ.get("ARR_STATUS_JELLYSEERR_SETTINGS_FILE")
    if override:
        return Path(override)
    return stack_home_directory() / "config" / "jellyseerr" / "settings.json"


def read_jellyseerr_api_key() -> str:
    settings_path = jellyseerr_settings_file()
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    api_key = settings.get("main", {}).get("apiKey", "")
    if not api_key:
        raise RuntimeError(f"Jellyseerr apiKey missing from {settings_path}")
    return api_key


def read_arr_bind_address() -> str | None:
    override = os.environ.get("ARR_STATUS_ARR_BIND_ADDRESS")
    if override:
        return override
    env_file = stack_home_directory() / ".env"
    if not env_file.is_file():
        return None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("ARR_BIND_ADDR="):
            return line.split("=", 1)[1].strip() or None
    return None


def read_app_api_key(app_name: str) -> str | None:
    config_path = stack_home_directory() / "config" / app_name / "config.xml"
    if not config_path.is_file():
        return None
    text = config_path.read_text(encoding="utf-8")
    start_marker = "<ApiKey>"
    end_marker = "</ApiKey>"
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1:
        return None
    return text[start + len(start_marker) : end].strip() or None


def app_endpoint(app_name, port, base_url_override_variable) -> ArrEndpoint | None:
    api_key = read_app_api_key(app_name)
    if api_key is None:
        return None
    base_url = os.environ.get(base_url_override_variable)
    if base_url is None:
        bind_address = read_arr_bind_address()
        if bind_address is None:
            return None
        base_url = f"http://{bind_address}:{port}"
    return ArrEndpoint(base_url=base_url, api_key=api_key)


def radarr_endpoint() -> ArrEndpoint | None:
    return app_endpoint("radarr", RADARR_PORT, "ARR_STATUS_RADARR_BASE_URL")


def sonarr_endpoint() -> ArrEndpoint | None:
    return app_endpoint("sonarr", SONARR_PORT, "ARR_STATUS_SONARR_BASE_URL")
