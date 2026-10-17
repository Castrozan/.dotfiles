import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest

specification = importlib.util.spec_from_file_location(
    "import_opencli_profile",
    Path(__file__).resolve().parents[2] / "import_opencli_profile.py",
)
module = importlib.util.module_from_spec(specification)
specification.loader.exec_module(module)


def test_import_preserves_source_and_excludes_runtime_files(tmp_path):
    source = tmp_path / "legacy"
    (source / "Default").mkdir(parents=True)
    (source / "Default/Cookies").write_bytes(b"cookie-fixture")
    (source / "SingletonCookie").write_text("stale")
    (source / ".pinchtab-state").mkdir()
    destination = tmp_path / "profiles/shorts"
    module.import_profile(source, destination)
    assert (source / "Default/Cookies").read_bytes() == b"cookie-fixture"
    assert (destination / "Default/Cookies").read_bytes() == b"cookie-fixture"
    assert not (destination / "SingletonCookie").exists()
    assert not (destination / ".pinchtab-state").exists()


def test_existing_destination_is_never_overwritten(tmp_path):
    source = tmp_path / "legacy"
    source.mkdir()
    (source / "session").write_text("old")
    destination = tmp_path / "current"
    destination.mkdir()
    (destination / "session").write_text("current")
    module.import_profile(source, destination)
    assert (destination / "session").read_text() == "current"


def test_live_source_is_not_copied(tmp_path, monkeypatch):
    source = tmp_path / "legacy"
    source.mkdir()
    (source / "SingletonLock").symlink_to(f"{module.socket.gethostname()}-123")
    monkeypatch.setattr(module.os, "kill", Mock())
    destination = tmp_path / "current"
    with pytest.raises(RuntimeError, match="Close the source"):
        module.import_profile(source, destination)
    assert not destination.exists()
