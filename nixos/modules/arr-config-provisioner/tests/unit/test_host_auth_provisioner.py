import sys
from pathlib import Path

PROVISIONER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_config_provisioner"
)
sys.path.insert(0, str(PROVISIONER_PACKAGE_DIRECTORY_PATH))

import host_auth_provisioner


def test_build_forms_authenticated_host_config_sets_login_and_preserves_rest():
    result = host_auth_provisioner.build_forms_authenticated_host_config(
        {"id": 1, "port": 7878, "authenticationMethod": "none"}, "lucas", "secret"
    )
    assert result["id"] == 1
    assert result["port"] == 7878
    assert result["authenticationMethod"] == "forms"
    assert result["authenticationRequired"] == "enabled"
    assert result["username"] == "lucas"
    assert result["password"] == "secret"
    assert result["passwordConfirmation"] == "secret"


def test_provision_host_login_skips_without_password(monkeypatch):
    calls = []
    monkeypatch.setattr(
        host_auth_provisioner,
        "update_host_config",
        lambda *args: calls.append(args),
    )
    outcome = host_auth_provisioner.provision_host_login(
        "http://host/api/v3", "key", "lucas", "", False
    )
    assert outcome == "skipped-missing-secret"
    assert calls == []


def test_provision_host_login_skips_without_username(monkeypatch):
    calls = []
    monkeypatch.setattr(
        host_auth_provisioner,
        "update_host_config",
        lambda *args: calls.append(args),
    )
    outcome = host_auth_provisioner.provision_host_login(
        "http://host/api/v3", "key", "", "secret", False
    )
    assert outcome == "skipped-missing-secret"
    assert calls == []


def test_provision_host_login_updates_with_current_config(monkeypatch):
    monkeypatch.setattr(
        host_auth_provisioner,
        "get_host_config",
        lambda base_url, api_key: {"id": 1, "authenticationMethod": "none"},
    )
    captured = {}
    monkeypatch.setattr(
        host_auth_provisioner,
        "update_host_config",
        lambda base_url, api_key, body: captured.update(body),
    )
    outcome = host_auth_provisioner.provision_host_login(
        "http://host/api/v3", "key", "lucas", "secret", False
    )
    assert outcome == "updated"
    assert captured["username"] == "lucas"
    assert captured["authenticationMethod"] == "forms"
    assert captured["password"] == "secret"


def test_provision_host_login_dry_run_does_not_update(monkeypatch):
    monkeypatch.setattr(
        host_auth_provisioner,
        "get_host_config",
        lambda base_url, api_key: {"id": 1},
    )
    calls = []
    monkeypatch.setattr(
        host_auth_provisioner,
        "update_host_config",
        lambda *args: calls.append(args),
    )
    outcome = host_auth_provisioner.provision_host_login(
        "http://host/api/v3", "key", "lucas", "secret", True
    )
    assert outcome == "would-update"
    assert calls == []
