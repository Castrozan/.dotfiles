import os
from pathlib import Path

from comet_stream_adapter import CometStreamAdapter
from managed_profile import MANAGED_PROFILE_CONFIGURATION


def required_environment_value(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def load_comet_adapter() -> CometStreamAdapter:
    configuration = next(
        addon["configuration"]
        for addon in MANAGED_PROFILE_CONFIGURATION["managedAddons"]
        if addon["manifest"]["id"] == "stremio.comet.fast"
    )
    secret_file = Path(required_environment_value("STREMIO_TORBOX_API_KEY_FILE"))
    return CometStreamAdapter(
        required_environment_value("STREMIO_COMET_URL"),
        configuration,
        secret_file.read_text(encoding="utf-8").strip(),
    )
