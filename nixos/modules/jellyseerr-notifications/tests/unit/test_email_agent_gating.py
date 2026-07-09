import json
import sys
from pathlib import Path

PATCH_SCRIPT_DIRECTORY_PATH = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(PATCH_SCRIPT_DIRECTORY_PATH))

import patch_jellyseerr_email_notifications as patcher

SENTINEL = "PENDING_GMAIL_APP_PASSWORD_SET_VIA_AGENIX"


def configuration_for(settings_file, app_password_secret_file, smtp_port=587):
    return {
        "settings_file": str(settings_file),
        "app_password_secret_file": str(app_password_secret_file),
        "app_password_sentinel": SENTINEL,
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


def email_agent_enabled(settings_file):
    return json.loads(settings_file.read_text())["notifications"]["agents"]["email"][
        "enabled"
    ]


def test_missing_secret_file_leaves_email_untouched(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    write_json(settings_file, disabled_email_settings())
    restarts = []
    monkeypatch.setattr(
        patcher,
        "restart_jellyseerr_best_effort",
        lambda binary, name: restarts.append(name),
    )
    changed = patcher.apply_email_notification_configuration(
        configuration_for(settings_file, tmp_path / "absent-secret")
    )
    assert changed is False
    assert restarts == []
    assert email_agent_enabled(settings_file) is False


def test_sentinel_password_leaves_email_untouched(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    write_json(settings_file, disabled_email_settings())
    secret_file = tmp_path / "secret"
    secret_file.write_text(SENTINEL + "\n", encoding="utf-8")
    monkeypatch.setattr(
        patcher, "restart_jellyseerr_best_effort", lambda binary, name: None
    )
    changed = patcher.apply_email_notification_configuration(
        configuration_for(settings_file, secret_file)
    )
    assert changed is False
    assert email_agent_enabled(settings_file) is False


def test_empty_secret_file_leaves_email_untouched(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    write_json(settings_file, disabled_email_settings())
    secret_file = tmp_path / "secret"
    secret_file.write_text("   \n", encoding="utf-8")
    monkeypatch.setattr(
        patcher, "restart_jellyseerr_best_effort", lambda binary, name: None
    )
    changed = patcher.apply_email_notification_configuration(
        configuration_for(settings_file, secret_file)
    )
    assert changed is False
    assert email_agent_enabled(settings_file) is False
