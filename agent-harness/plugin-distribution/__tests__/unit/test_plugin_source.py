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


@pytest.mark.parametrize("targets", [("hermes",), ("typo",), ()])
def test_unsupported_targets_fail_before_building(source, targets):
    with pytest.raises(ValueError, match="Unsupported targets"):
        read_portable_plugin(source, targets)


def test_pi_cannot_silently_drop_mcp(source):
    with pytest.raises(ValueError, match="Pi projection supports skills only"):
        read_portable_plugin(source, ("pi",))
    (source / "mcp.json").unlink()
    assert read_portable_plugin(source, ("pi",)) == "distribution-probe"


@pytest.mark.parametrize("component", ["AGENTS.md", "commands", "hooks", "agents"])
def test_native_components_require_an_adapter(source, component):
    (source / component).touch()
    with pytest.raises(ValueError, match="explicit adapters"):
        read_portable_plugin(source, ("claude",))


def test_extension_is_not_silently_ignored(source):
    path = source / "plugin.json"
    manifest = json.loads(path.read_text())
    manifest["extensions"] = {"com.example.client": {"hooks": "./hook.json"}}
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="explicit adapters"):
        read_portable_plugin(source, ("codex",))


def test_file_only_extension_is_not_silently_ignored(source):
    (source / "com.example.client").mkdir()
    with pytest.raises(ValueError, match="explicit adapters"):
        read_portable_plugin(source, ("codex",))


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


def test_directory_symlink_cycle_is_rejected(source):
    (source / "cycle").symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="directory"):
        read_portable_plugin(source, ("claude",))


def test_opencode_writable_data_requirement_is_rejected(source):
    path = source / "mcp.json"
    path.write_text(path.read_text().replace("${PLUGIN_ROOT}", "${PLUGIN_DATA}"))
    with pytest.raises(ValueError, match="writable runtime directory"):
        read_portable_plugin(source, ("opencode",))


@pytest.mark.parametrize("manifest", [{"name": "legacy"}, []])
def test_other_manifest_formats_need_explicit_importers(source, manifest):
    (source / "plugin.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Agent Plugins v1"):
        read_portable_plugin(source, ("claude",))
