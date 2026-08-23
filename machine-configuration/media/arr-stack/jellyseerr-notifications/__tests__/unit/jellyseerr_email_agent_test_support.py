import json

APP_PASSWORD_SENTINEL = "PENDING_GMAIL_APP_PASSWORD_SET_VIA_AGENIX"


def configuration_for(settings_file, app_password_secret_file, smtp_port=587):
    return {
        "settings_file": str(settings_file),
        "app_password_secret_file": str(app_password_secret_file),
        "app_password_sentinel": APP_PASSWORD_SENTINEL,
        "sender_address": "castro.lucas290@gmail.com",
        "sender_name": "Jellyseerr Requests",
        "smtp_host": "smtp.gmail.com",
        "smtp_port": smtp_port,
        "smtp_username": "castro.lucas290@gmail.com",
        "notification_types_bitmask": 2,
        "docker_binary": "docker",
        "container_name": "arr-jellyseerr",
    }


def disabled_email_settings():
    return {
        "notifications": {
            "agents": {
                "email": {"enabled": False, "options": {"senderName": "Jellyseerr"}}
            }
        }
    }


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
