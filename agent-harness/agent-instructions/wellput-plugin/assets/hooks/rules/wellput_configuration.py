import json
import os
from pathlib import Path


def configuration_path():
    explicit_path = os.environ.get("WELLPUT_CONFIG")
    if explicit_path is not None:
        return Path(explicit_path).expanduser()
    configuration_home = Path(
        os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    )
    user_path = configuration_home / "wellput/config.json"
    if user_path.exists():
        return user_path
    return Path(__file__).resolve().parents[2] / "wellput.json"


def load_configuration_document():
    path = configuration_path()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(
            f"Cannot load Wellput configuration at {path}: {error}"
        ) from error
