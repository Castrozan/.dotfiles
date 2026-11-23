import json
import shutil
from pathlib import Path

import pytest

from portable_plugin import read_portable_plugin


FIXTURE = Path(__file__).parents[1] / "fixtures" / "portable-plugin"


@pytest.fixture
def source(tmp_path):
    return Path(shutil.copytree(FIXTURE, tmp_path / "plugin"))


def test_portable_plugin_accepts_all_complete_targets(source):
    assert read_portable_plugin(source, ("claude", "codex", "opencode")) == (
        "distribution-probe"
    )


@pytest.mark.parametrize("targets", [("typo",)])
def test_unsupported_targets_fail_before_building(source, targets):
    with pytest.raises(ValueError, match="Unsupported targets"):
        read_portable_plugin(source, targets)


@pytest.mark.parametrize("targets", [("pi",), ("hermes",), ()])
def test_whole_package_loaders_accept_mcp(source, targets):
    assert read_portable_plugin(source, targets) == "distribution-probe"


@pytest.mark.parametrize("name", ["../escape", "two--hyphens", "", ["invalid"]])
def test_invalid_plugin_identity_is_rejected(source, name):
    path = source / "plugin.json"
    manifest = json.loads(path.read_text())
    manifest["name"] = name
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Invalid portable plugin name"):
        read_portable_plugin(source, ("claude",))


def test_external_symlink_is_not_materialized(source, tmp_path):
    outside = tmp_path / "private"
    outside.write_text("must not enter the artifact")
    (source / "external").symlink_to(outside)
    with pytest.raises(ValueError, match="external symlinks"):
        read_portable_plugin(source, ("claude",))


@pytest.mark.parametrize("manifest", [{"name": "legacy"}, []])
def test_other_manifest_formats_need_explicit_importers(source, manifest):
    (source / "plugin.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Agent Plugins v1"):
        read_portable_plugin(source, ("claude",))
