import json
import sys
from pathlib import Path

import pytest

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import runtime_credentials


def test_read_jellyfin_api_key_reads_and_strips(tmp_path, monkeypatch):
    secret_file = tmp_path / "jellyfin-admin-api-key"
    secret_file.write_text("abc123\n", encoding="utf-8")
    monkeypatch.setenv("ARR_USERS_JELLYFIN_API_KEY_FILE", str(secret_file))
    assert runtime_credentials.read_jellyfin_api_key() == "abc123"


def test_read_jellyfin_api_key_exits_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("ARR_USERS_JELLYFIN_API_KEY_FILE", str(tmp_path / "absent"))
    with pytest.raises(SystemExit):
        runtime_credentials.read_jellyfin_api_key()


def test_read_jellyfin_api_key_exits_when_file_empty(tmp_path, monkeypatch):
    secret_file = tmp_path / "jellyfin-admin-api-key"
    secret_file.write_text("   \n", encoding="utf-8")
    monkeypatch.setenv("ARR_USERS_JELLYFIN_API_KEY_FILE", str(secret_file))
    with pytest.raises(SystemExit):
        runtime_credentials.read_jellyfin_api_key()


def test_read_jellyseerr_api_key_extracts_from_settings(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"main": {"apiKey": "seerr-key"}}))
    monkeypatch.setenv("ARR_USERS_JELLYSEERR_SETTINGS_FILE", str(settings_file))
    assert runtime_credentials.read_jellyseerr_api_key() == "seerr-key"


def test_read_jellyseerr_api_key_exits_when_key_absent(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"main": {}}))
    monkeypatch.setenv("ARR_USERS_JELLYSEERR_SETTINGS_FILE", str(settings_file))
    with pytest.raises(SystemExit):
        runtime_credentials.read_jellyseerr_api_key()


def test_read_jellyseerr_api_key_exits_when_settings_missing(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "ARR_USERS_JELLYSEERR_SETTINGS_FILE", str(tmp_path / "absent.json")
    )
    with pytest.raises(SystemExit):
        runtime_credentials.read_jellyseerr_api_key()


def test_base_urls_fall_back_to_loopback_defaults(monkeypatch):
    monkeypatch.delenv("ARR_USERS_JELLYFIN_BASE_URL", raising=False)
    monkeypatch.delenv("ARR_USERS_JELLYSEERR_BASE_URL", raising=False)
    assert runtime_credentials.jellyfin_base_url().startswith("http://127.0.0.1")
    assert runtime_credentials.jellyseerr_base_url().startswith("http://127.0.0.1")
