import json
import sys
from pathlib import Path

from jellyseerr_email_agent_test_support import (
    configuration_for,
    disabled_email_settings,
    write_json,
)

PATCH_SCRIPT_DIRECTORY_PATH = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(PATCH_SCRIPT_DIRECTORY_PATH))

import patch_jellyseerr_email_notifications as patcher


def written_agents(settings_file):
    return json.loads(settings_file.read_text())["notifications"]["agents"]


def test_real_password_enables_and_configures_email_agent(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    write_json(settings_file, disabled_email_settings())
    secret_file = tmp_path / "secret"
    secret_file.write_text("abcd efgh ijkl mnop\n", encoding="utf-8")
    restarts = []
    monkeypatch.setattr(
        patcher,
        "restart_jellyseerr_best_effort",
        lambda binary, name: restarts.append(name),
    )
    changed = patcher.apply_email_notification_configuration(
        configuration_for(settings_file, secret_file)
    )
    assert changed is True
    assert restarts == ["arr-jellyseerr"]
    email_agent = written_agents(settings_file)["email"]
    assert email_agent["enabled"] is True
    assert email_agent["types"] == 2
    options = email_agent["options"]
    assert options["authPass"] == "abcd efgh ijkl mnop"
    assert options["authUser"] == "castro.lucas290@gmail.com"
    assert options["emailFrom"] == "castro.lucas290@gmail.com"
    assert options["smtpHost"] == "smtp.gmail.com"
    assert options["smtpPort"] == 587
    assert options["secure"] is False
    assert options["requireTls"] is True
    assert options["senderName"] == "Jellyseerr Requests"


def test_implicit_tls_derived_for_port_465(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    write_json(settings_file, disabled_email_settings())
    secret_file = tmp_path / "secret"
    secret_file.write_text("app-password", encoding="utf-8")
    monkeypatch.setattr(
        patcher, "restart_jellyseerr_best_effort", lambda binary, name: None
    )
    patcher.apply_email_notification_configuration(
        configuration_for(settings_file, secret_file, smtp_port=465)
    )
    options = written_agents(settings_file)["email"]["options"]
    assert options["secure"] is True
    assert options["requireTls"] is False


def test_idempotent_second_run_does_not_rewrite_or_restart(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    write_json(settings_file, disabled_email_settings())
    secret_file = tmp_path / "secret"
    secret_file.write_text("app-password", encoding="utf-8")
    restarts = []
    monkeypatch.setattr(
        patcher,
        "restart_jellyseerr_best_effort",
        lambda binary, name: restarts.append(name),
    )
    configuration = configuration_for(settings_file, secret_file)
    assert patcher.apply_email_notification_configuration(configuration) is True
    assert patcher.apply_email_notification_configuration(configuration) is False
    assert restarts == ["arr-jellyseerr"]


def test_preserves_foreign_option_keys_and_sibling_agents(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    write_json(
        settings_file,
        {
            "notifications": {
                "agents": {
                    "email": {
                        "enabled": False,
                        "options": {
                            "senderName": "Jellyseerr",
                            "pgpPrivateKey": "PRESERVE-THIS-KEY",
                        },
                    },
                    "webhook": {
                        "enabled": True,
                        "options": {"webhookUrl": "http://hook.local"},
                    },
                }
            }
        },
    )
    secret_file = tmp_path / "secret"
    secret_file.write_text("app-password", encoding="utf-8")
    monkeypatch.setattr(
        patcher, "restart_jellyseerr_best_effort", lambda binary, name: None
    )
    patcher.apply_email_notification_configuration(
        configuration_for(settings_file, secret_file)
    )
    agents = written_agents(settings_file)
    assert agents["email"]["options"]["pgpPrivateKey"] == "PRESERVE-THIS-KEY"
    assert agents["webhook"] == {
        "enabled": True,
        "options": {"webhookUrl": "http://hook.local"},
    }


def test_apply_succeeds_even_when_container_restart_fails(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    write_json(settings_file, disabled_email_settings())
    secret_file = tmp_path / "secret"
    secret_file.write_text("app-password", encoding="utf-8")

    class FailedDockerRun:
        returncode = 1
        stderr = "Error: No such container: arr-jellyseerr"

    monkeypatch.setattr(
        patcher.subprocess, "run", lambda *args, **kwargs: FailedDockerRun()
    )
    changed = patcher.apply_email_notification_configuration(
        configuration_for(settings_file, secret_file)
    )
    assert changed is True
    assert written_agents(settings_file)["email"]["enabled"] is True
