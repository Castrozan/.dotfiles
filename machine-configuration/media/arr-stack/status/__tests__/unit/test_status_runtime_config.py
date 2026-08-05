import json
import sys
from pathlib import Path

import pytest

ARR_STATUS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_status"
)
sys.path.insert(0, str(ARR_STATUS_PACKAGE_DIRECTORY_PATH))

import status_runtime_config


def write_stack(tmp_path, bind_line="ARR_BIND_ADDR=10.0.0.5"):
    (tmp_path / "config" / "jellyseerr").mkdir(parents=True)
    (tmp_path / "config" / "jellyseerr" / "settings.json").write_text(
        json.dumps({"main": {"apiKey": "seer-key"}})
    )
    (tmp_path / "config" / "radarr").mkdir(parents=True)
    (tmp_path / "config" / "radarr" / "config.xml").write_text(
        "<Config><ApiKey>rad-key</ApiKey></Config>"
    )
    (tmp_path / ".env").write_text(f"PUID=1000\n{bind_line}\n")


def test_read_jellyseerr_api_key(tmp_path, monkeypatch):
    write_stack(tmp_path)
    monkeypatch.setenv("ARR_STATUS_STACK_HOME", str(tmp_path))
    monkeypatch.delenv("ARR_STATUS_JELLYSEERR_SETTINGS_FILE", raising=False)
    assert status_runtime_config.read_jellyseerr_api_key() == "seer-key"


def test_read_jellyseerr_api_key_raises_when_absent(tmp_path, monkeypatch):
    (tmp_path / "config" / "jellyseerr").mkdir(parents=True)
    (tmp_path / "config" / "jellyseerr" / "settings.json").write_text(
        json.dumps({"main": {}})
    )
    monkeypatch.setenv("ARR_STATUS_STACK_HOME", str(tmp_path))
    monkeypatch.delenv("ARR_STATUS_JELLYSEERR_SETTINGS_FILE", raising=False)
    with pytest.raises(RuntimeError):
        status_runtime_config.read_jellyseerr_api_key()


def test_read_arr_bind_address_from_env_file(tmp_path, monkeypatch):
    write_stack(tmp_path)
    monkeypatch.setenv("ARR_STATUS_STACK_HOME", str(tmp_path))
    monkeypatch.delenv("ARR_STATUS_ARR_BIND_ADDRESS", raising=False)
    assert status_runtime_config.read_arr_bind_address() == "10.0.0.5"


def test_read_arr_bind_address_none_when_missing(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("PUID=1000\n")
    monkeypatch.setenv("ARR_STATUS_STACK_HOME", str(tmp_path))
    monkeypatch.delenv("ARR_STATUS_ARR_BIND_ADDRESS", raising=False)
    assert status_runtime_config.read_arr_bind_address() is None


def test_read_app_api_key_from_config_xml(tmp_path, monkeypatch):
    write_stack(tmp_path)
    monkeypatch.setenv("ARR_STATUS_STACK_HOME", str(tmp_path))
    assert status_runtime_config.read_app_api_key("radarr") == "rad-key"


def test_radarr_endpoint_builds_base_url_from_bind(tmp_path, monkeypatch):
    write_stack(tmp_path)
    monkeypatch.setenv("ARR_STATUS_STACK_HOME", str(tmp_path))
    monkeypatch.delenv("ARR_STATUS_ARR_BIND_ADDRESS", raising=False)
    monkeypatch.delenv("ARR_STATUS_RADARR_BASE_URL", raising=False)
    endpoint = status_runtime_config.radarr_endpoint()
    assert endpoint.base_url == "http://10.0.0.5:7878"
    assert endpoint.api_key == "rad-key"


def test_sonarr_endpoint_none_when_api_key_missing(tmp_path, monkeypatch):
    write_stack(tmp_path)
    monkeypatch.setenv("ARR_STATUS_STACK_HOME", str(tmp_path))
    assert status_runtime_config.sonarr_endpoint() is None


def test_radarr_endpoint_none_when_bind_missing(tmp_path, monkeypatch):
    write_stack(tmp_path, bind_line="OTHER=1")
    monkeypatch.setenv("ARR_STATUS_STACK_HOME", str(tmp_path))
    monkeypatch.delenv("ARR_STATUS_ARR_BIND_ADDRESS", raising=False)
    monkeypatch.delenv("ARR_STATUS_RADARR_BASE_URL", raising=False)
    assert status_runtime_config.radarr_endpoint() is None
