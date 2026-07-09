import json
import sys
from pathlib import Path

import pytest

PROVISIONER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_config_provisioner"
)
sys.path.insert(0, str(PROVISIONER_PACKAGE_DIRECTORY_PATH))

import runtime_config


def test_read_app_api_key_extracts_key(tmp_path):
    (tmp_path / "radarr").mkdir()
    (tmp_path / "radarr" / "config.xml").write_text(
        "<Config><ApiKey>abc123</ApiKey></Config>", encoding="utf-8"
    )
    assert runtime_config.read_app_api_key(str(tmp_path), "radarr") == "abc123"


def test_read_app_api_key_raises_runtimeerror_when_key_absent(tmp_path):
    (tmp_path / "radarr").mkdir()
    (tmp_path / "radarr" / "config.xml").write_text(
        "<Config></Config>", encoding="utf-8"
    )
    with pytest.raises(RuntimeError):
        runtime_config.read_app_api_key(str(tmp_path), "radarr")


def test_required_environment_value_raises_on_missing_and_empty(monkeypatch):
    monkeypatch.delenv("ARR_PROVISIONER_PROBE", raising=False)
    with pytest.raises(SystemExit):
        runtime_config.required_environment_value("ARR_PROVISIONER_PROBE")
    monkeypatch.setenv("ARR_PROVISIONER_PROBE", "")
    with pytest.raises(SystemExit):
        runtime_config.required_environment_value("ARR_PROVISIONER_PROBE")


def test_read_bind_address_raises_when_key_missing(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=1\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        runtime_config.read_bind_address(str(env_file), "ARR_BIND_ADDR")


def test_substitute_secrets_replaces_exact_token_only():
    body = {
        "fields": [
            {"name": "password", "value": "@QBITTORRENT_PASSWORD@"},
            {"name": "host", "value": "qbittorrent"},
        ]
    }
    out = runtime_config.substitute_secrets(body, {"@QBITTORRENT_PASSWORD@": "s3cret"})
    assert out["fields"][0]["value"] == "s3cret"
    assert out["fields"][1]["value"] == "qbittorrent"


def test_contains_unresolved_secret_token_detects_placeholder():
    assert (
        runtime_config.contains_unresolved_secret_token({"a": [{"v": "@X@"}]}) is True
    )
    assert runtime_config.contains_unresolved_secret_token({"a": "plain"}) is False


def test_build_secret_map_excludes_missing_and_empty(tmp_path):
    present = tmp_path / "present"
    present.write_text("value", encoding="utf-8")
    absent = tmp_path / "absent"
    secret_map = runtime_config.build_secret_map(
        [("@A@", str(present)), ("@B@", str(absent))]
    )
    assert secret_map == {"@A@": "value"}


def test_read_bind_address_from_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=1\nARR_BIND_ADDR=100.94.11.81\n", encoding="utf-8")
    assert (
        runtime_config.read_bind_address(str(env_file), "ARR_BIND_ADDR")
        == "100.94.11.81"
    )


def test_load_desired_objects_substitutes_secrets(tmp_path):
    radarr_directory = tmp_path / "radarr"
    radarr_directory.mkdir()
    (radarr_directory / "downloadclient.json").write_text(
        json.dumps(
            [
                {
                    "name": "qBittorrent",
                    "fields": [{"name": "password", "value": "@QBITTORRENT_PASSWORD@"}],
                }
            ]
        ),
        encoding="utf-8",
    )
    out = runtime_config.load_desired_objects(
        str(tmp_path), "radarr", "downloadclient", {"@QBITTORRENT_PASSWORD@": "pw"}
    )
    assert out[0]["fields"][0]["value"] == "pw"
