import os
import sys

from provisioner_core import provision_all
from runtime_config import (
    build_secret_map,
    read_bind_address,
    read_secret_value,
    required_environment_value,
)


def resolve_login_passwords():
    return {
        "radarr": read_secret_value(
            os.environ.get("ARR_PROVISIONER_RADARR_PASSWORD_FILE", "")
        ),
        "sonarr": read_secret_value(
            os.environ.get("ARR_PROVISIONER_SONARR_PASSWORD_FILE", "")
        ),
        "prowlarr": read_secret_value(
            os.environ.get("ARR_PROVISIONER_PROWLARR_PASSWORD_FILE", "")
        ),
    }


def resolve_configuration():
    env_file = required_environment_value("ARR_PROVISIONER_ENV_FILE")
    return {
        "bind_address": read_bind_address(
            env_file, required_environment_value("ARR_BIND_ADDRESS_KEY")
        ),
        "config_root": required_environment_value("ARR_PROVISIONER_CONFIG_ROOT"),
        "desired_state_dir": required_environment_value(
            "ARR_PROVISIONER_DESIRED_STATE_DIR"
        ),
        "login_username": os.environ.get("ARR_PROVISIONER_LOGIN_USERNAME", ""),
        "login_passwords": resolve_login_passwords(),
        "secret_map": build_secret_map(
            [
                (
                    "@QBITTORRENT_PASSWORD@",
                    os.environ.get("ARR_PROVISIONER_QBITTORRENT_PASSWORD_FILE", ""),
                ),
                (
                    "@SAMARITANO_APIKEY@",
                    os.environ.get("ARR_PROVISIONER_SAMARITANO_APIKEY_FILE", ""),
                ),
            ]
        ),
    }


def main():
    dry_run = "--dry-run" in sys.argv[1:]
    provision_all(resolve_configuration(), dry_run)


if __name__ == "__main__":
    main()
