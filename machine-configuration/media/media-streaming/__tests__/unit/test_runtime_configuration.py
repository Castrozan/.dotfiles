import importlib
import sys
from pathlib import Path

import pytest


PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "stremio_gateway"
)
sys.path.insert(0, str(PACKAGE_DIRECTORY_PATH))
runtime_configuration = importlib.import_module("runtime_configuration")


def test_runtime_reads_the_agenix_key_and_fails_without_credentials(
    tmp_path, monkeypatch
):
    secret_file = tmp_path / "torbox-api-key"
    monkeypatch.setenv("STREMIO_COMET_URL", "http://100.64.0.1:43214")
    monkeypatch.setenv("STREMIO_TORBOX_API_KEY_FILE", str(secret_file))
    with pytest.raises(FileNotFoundError):
        runtime_configuration.load_comet_adapter()
    secret_file.write_text("\n")
    with pytest.raises(ValueError, match="TorBox API key is missing"):
        runtime_configuration.load_comet_adapter()
    secret_file.write_text("runtime-key\n")
    adapter = runtime_configuration.load_comet_adapter()
    assert adapter.comet_url == "http://100.64.0.1:43214"
    assert "runtime-key" not in adapter.public_configuration
