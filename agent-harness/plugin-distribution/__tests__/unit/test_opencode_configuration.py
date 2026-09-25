import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from opencode_mcp import write_opencode_configuration


def prepare_configuration(output, name, revision):
    plugin = output / ".agents/plugins" / name
    plugin.mkdir(parents=True)
    data = output / ".agents/plugin-data" / name
    data.mkdir(parents=True)
    configuration = output / ".opencode/opencode.jsonc"
    configuration.parent.mkdir()
    server = {
        "type": "local",
        "command": [
            sys.executable,
            "-c",
            'import os,pathlib,sys; p=pathlib.Path(os.environ["PLUGIN_DATA"])/"state"; '
            'p.write_text((p.read_text() if p.exists() else "")+sys.argv[1]); print(p)',
            revision,
        ],
        "cwd": str(data),
        "environment": {"PLUGIN_ROOT": str(plugin), "PLUGIN_DATA": str(data)},
    }
    configuration.write_text(json.dumps({"mcp": {f"plugin.{name}.state": server}}))
    return configuration, server


def test_native_state_survives_revisions_and_remains_separate_between_plugins(tmp_path):
    state_root = tmp_path / 'writable "state"'
    for name in ("first-plugin", "second-plugin"):
        for revision in ("first", "second"):
            output = tmp_path / name / revision
            configuration, original = prepare_configuration(output, name, revision)
            write_opencode_configuration(output, name, state_root)
            if name == "first-plugin" and revision == "first":
                assert not state_root.exists()
            data = state_root / name
            data.mkdir(parents=True, exist_ok=True)
            emitted = json.loads(configuration.read_text())["mcp"][
                f"plugin.{name}.state"
            ]
            assert emitted["command"] == original["command"]
            result = subprocess.run(
                emitted["command"],
                cwd=emitted["cwd"],
                env=os.environ | emitted["environment"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            assert Path(result.stdout.strip()) == data / "state"
            assert not (output / ".agents/plugin-data" / name / "state").exists()
        assert (state_root / name / "state").read_text() == "firstsecond"


def test_projection_relocates_data_references_and_preserves_native_fields(tmp_path):
    configuration, original = prepare_configuration(
        tmp_path / "bundle", "example", "first"
    )
    old_data = original["environment"]["PLUGIN_DATA"]
    original["command"] = [
        "native-server",
        old_data + "/config",
        "$(exit 99)",
        "${HOME}",
    ]
    original["environment"]["CONFIG"] = old_data + "/settings.json"
    configuration.write_text(json.dumps({"mcp": {"plugin.example.state": original}}))
    state_root = tmp_path / "state"
    write_opencode_configuration(tmp_path / "bundle", "example", state_root)
    emitted = json.loads(configuration.read_text())["mcp"]["plugin.example.state"]
    assert emitted["command"] == [
        "native-server",
        str(state_root / "example/config"),
        "$(exit 99)",
        "${HOME}",
    ]
    assert emitted["environment"]["CONFIG"] == str(state_root / "example/settings.json")
    assert (
        emitted["environment"]["PLUGIN_ROOT"] == original["environment"]["PLUGIN_ROOT"]
    )
    assert emitted["environment"]["PLUGIN_DATA"] == str(state_root / "example")
    assert emitted["cwd"] == str(state_root / "example")


def test_remote_server_and_opaque_native_substitution_syntax_stay_literal(tmp_path):
    path = tmp_path / ".opencode/opencode.jsonc"
    path.parent.mkdir()
    server = {
        "type": "remote",
        "url": "https://example.com/mcp",
        "headers": {"opaque": "{env:UNRELATED} {file:absent}"},
    }
    path.write_text(json.dumps({"mcp": {"remote": server}}))
    write_opencode_configuration(tmp_path, "example", tmp_path.parent / "state")
    assert json.loads(path.read_text())["mcp"]["remote"] == server
    assert "{env:UNRELATED}" not in path.read_text()
    assert "{file:absent}" not in path.read_text()


def test_skill_only_package_has_immutable_discovery_configuration(tmp_path):
    skills = tmp_path / ".agents/plugins/example/skills"
    skills.mkdir(parents=True)
    write_opencode_configuration(tmp_path, "example", tmp_path.parent / "state")
    configuration = json.loads((tmp_path / ".opencode/opencode.jsonc").read_text())
    assert configuration["$schema"] == "https://opencode.ai/config.json"
    assert configuration["skills"]["paths"] == [str(skills)]


@pytest.mark.parametrize("data_root", ["relative", "inside-package"])
def test_state_requires_an_absolute_directory_outside_the_bundle(tmp_path, data_root):
    root = Path("relative") if data_root == "relative" else tmp_path / "data"
    with pytest.raises(ValueError, match="OpenCode plugin data"):
        write_opencode_configuration(tmp_path, "example", root)
