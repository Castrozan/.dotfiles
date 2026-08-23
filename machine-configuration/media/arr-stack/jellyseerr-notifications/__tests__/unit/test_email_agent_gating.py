import json
import sys
from pathlib import Path

from jellyseerr_email_agent_test_support import (
    APP_PASSWORD_SENTINEL,
    configuration_for,
    disabled_email_settings,
    write_json,
)

PATCH_SCRIPT_DIRECTORY_PATH = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(PATCH_SCRIPT_DIRECTORY_PATH))

import patch_jellyseerr_email_notifications as patcher


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
    secret_file.write_text(APP_PASSWORD_SENTINEL + "\n", encoding="utf-8")
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
