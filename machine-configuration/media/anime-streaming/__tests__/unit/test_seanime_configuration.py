import sys
from pathlib import Path

import pytest

PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "seanime_provisioner"
)
sys.path.insert(0, str(PACKAGE_DIRECTORY_PATH))

import seanime_configuration


def test_torrent_streaming_uses_transient_cache_without_library_import():
    current = {
        "id": 1,
        "enabled": False,
        "downloadDir": "/persistent/downloads",
        "addToLibrary": True,
        "includeInLibrary": True,
        "preloadNextStream": True,
        "preferredResolution": "1080",
    }

    desired = seanime_configuration.desired_torrentstream_settings(
        current, "100.64.0.1"
    )

    assert desired["id"] == 1
    assert desired["enabled"] is True
    assert desired["downloadDir"] == ""
    assert desired["addToLibrary"] is False
    assert desired["includeInLibrary"] is False
    assert desired["preloadNextStream"] is False
    assert desired["torrentClientHost"] == "100.64.0.1"
    assert desired["streamingServerHost"] == "127.0.0.1"
    assert desired["preferredResolution"] == "1080"


def test_provider_configuration_keeps_the_runtime_api_key_out_of_declarations():
    config = seanime_configuration.provider_user_config(
        "runtime-secret", "http://100.64.0.1:9696"
    )

    assert config == {
        "id": "prowlarr-torrent-provider",
        "version": 1,
        "values": {
            "prowlarrBaseUrl": "http://100.64.0.1:9696",
            "prowlarrApiKey": "runtime-secret",
            "resultLimit": "50",
        },
    }


def test_prowlarr_api_key_is_read_from_the_runtime_config(tmp_path):
    config_file = tmp_path / "config.xml"
    config_file.write_text(
        "<Config><ApiKey>runtime-secret</ApiKey></Config>", encoding="utf-8"
    )

    assert seanime_configuration.read_prowlarr_api_key(config_file) == "runtime-secret"


def test_missing_prowlarr_api_key_refuses_to_provision(tmp_path):
    config_file = tmp_path / "config.xml"
    config_file.write_text("<Config></Config>", encoding="utf-8")

    with pytest.raises(RuntimeError, match="API key is missing"):
        seanime_configuration.read_prowlarr_api_key(config_file)
