import os
import sys
import time

from download_chain_control import compose_base_command
from runtime_environment import (
    read_arr_bind_address_from_env_file,
    read_jellyseerr_api_key,
    required_environment_value,
)
from supervisor_core import run_supervisor_tick


def resolve_disk_guard_configuration():
    return {
        "path": required_environment_value("ARR_DISK_GUARD_PATH"),
        "warning_gigabytes": float(
            required_environment_value("ARR_DISK_GUARD_WARNING_GIGABYTES")
        ),
        "critical_gigabytes": float(
            required_environment_value("ARR_DISK_GUARD_CRITICAL_GIGABYTES")
        ),
        "fill_service": required_environment_value("ARR_DISK_GUARD_FILL_SERVICE"),
        "critical_reminder_seconds": int(
            required_environment_value("ARR_DISK_GUARD_CRITICAL_REMINDER_SECONDS")
        ),
        "alert_state_file": required_environment_value(
            "ARR_DISK_GUARD_ALERT_STATE_FILE"
        ),
        "smtp_host": required_environment_value("ARR_DISK_ALERT_SMTP_HOST"),
        "smtp_port": int(required_environment_value("ARR_DISK_ALERT_SMTP_PORT")),
        "smtp_username": os.environ.get("ARR_DISK_ALERT_SMTP_USERNAME", ""),
        "email_sender": os.environ.get("ARR_DISK_ALERT_EMAIL_SENDER", ""),
        "email_recipient": os.environ.get("ARR_DISK_ALERT_EMAIL_RECIPIENT", ""),
        "app_password_file": os.environ.get("ARR_DISK_ALERT_APP_PASSWORD_FILE", ""),
    }


def resolve_configuration():
    env_file = required_environment_value("ARR_ENV_FILE")
    bind_address = read_arr_bind_address_from_env_file(
        env_file, required_environment_value("ARR_BIND_ADDRESS_KEY")
    )
    radarr_port = required_environment_value("RADARR_PORT")
    sonarr_port = required_environment_value("SONARR_PORT")
    return {
        "base_command": compose_base_command(
            required_environment_value("DOCKER_COMPOSE_BIN"),
            required_environment_value("ARR_COMPOSE_FILE"),
            env_file,
            required_environment_value("ARR_PROJECT_DIRECTORY"),
            required_environment_value("ARR_COMPOSE_PROJECT"),
        ),
        "on_demand_services": required_environment_value(
            "ARR_ON_DEMAND_SERVICES"
        ).split(),
        "idle_grace_seconds": int(required_environment_value("ARR_IDLE_GRACE_SECONDS")),
        "keep_chain_always_on": required_environment_value("ARR_KEEP_CHAIN_ALWAYS_ON")
        == "true",
        "recent_pending_window_seconds": int(
            required_environment_value("ARR_RECENT_PENDING_WINDOW_SECONDS")
        ),
        "state_file_path": required_environment_value("ARR_STATE_FILE"),
        "jellyseerr_url": required_environment_value("JELLYSEERR_URL"),
        "jellyseerr_api_key": read_jellyseerr_api_key(
            required_environment_value("JELLYSEERR_SETTINGS_FILE")
        ),
        "radarr_url": f"http://{bind_address}:{radarr_port}",
        "sonarr_url": f"http://{bind_address}:{sonarr_port}",
        "radarr_config_file": required_environment_value("RADARR_CONFIG_FILE"),
        "sonarr_config_file": required_environment_value("SONARR_CONFIG_FILE"),
        "disk_guard": resolve_disk_guard_configuration(),
    }


def main():
    dry_run = "--dry-run" in sys.argv[1:]
    run_supervisor_tick(resolve_configuration(), time.time(), dry_run)


if __name__ == "__main__":
    main()
