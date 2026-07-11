ON_DEMAND_SERVICES = ["radarr", "sonarr", "prowlarr", "qbittorrent", "bazarr"]


def disk_guard_config(tmp_path, mount_guard_enabled=True):
    return {
        "path": str(tmp_path),
        "warning_gigabytes": 30,
        "critical_gigabytes": 15,
        "fill_service": "qbittorrent",
        "critical_reminder_seconds": 21600,
        "alert_state_file": str(tmp_path / "alert-state.json"),
        "mount_guard_enabled": mount_guard_enabled,
        "mount_alert_state_file": str(tmp_path / "mount-alert-state.json"),
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_username": "",
        "email_sender": "",
        "email_recipient": "",
        "app_password_file": "",
    }


def base_configuration(tmp_path, mount_guard_enabled=True):
    return {
        "base_command": ["compose"],
        "on_demand_services": ON_DEMAND_SERVICES,
        "disk_guard": disk_guard_config(tmp_path, mount_guard_enabled),
    }
