import json
import os
import sys
import tempfile

from native_opencode_server import native_server
from pathlib import Path


def verify_configuration(executable, settings, plugin_settings, bundle, data_root):
    global_configuration = json.loads(settings.read_text())
    emitted_configuration = json.loads(
        (bundle / ".opencode/opencode.jsonc").read_text()
    )
    installed_configuration = json.loads(plugin_settings.read_text())
    installed_servers = {
        name: server.copy() for name, server in installed_configuration["mcp"].items()
    }
    expected_timeouts = {
        "plugin.dotfiles.chrome-devtools": 120000,
    }
    assert "mcp" not in global_configuration
    assert "skills" not in global_configuration
    for name, timeout in expected_timeouts.items():
        assert installed_configuration["mcp"][name].pop("timeout") == timeout
        server = emitted_configuration["mcp"][name]
        assert server["command"][0] == str(
            bundle / ".agents/plugins/dotfiles/native/mcp" / name.split(".")[-1]
        )
        assert server["environment"]["PLUGIN_DATA"] == str(data_root / "dotfiles")
        assert not (data_root / "dotfiles").is_relative_to(bundle)
    assert installed_configuration == emitted_configuration

    with tempfile.TemporaryDirectory(
        prefix="opencode-native-configuration-"
    ) as temporary:
        root = Path(temporary)
        configuration = root / "config/opencode"
        configuration.mkdir(parents=True)
        (configuration / "opencode.json").symlink_to(settings)
        (configuration / "opencode.jsonc").symlink_to(plugin_settings)
        overlay = root / "overlay.json"
        overlay.write_text(
            json.dumps(
                {
                    "instructions": ["native-configuration-overlay.md"],
                    "mcp": {
                        name: server | {"enabled": False}
                        for name, server in installed_servers.items()
                    },
                }
            )
        )
        environment = {
            "PATH": os.environ["PATH"],
            "HOME": str(root),
            "XDG_CONFIG_HOME": str(root / "config"),
            "XDG_CACHE_HOME": str(root / "cache"),
            "XDG_DATA_HOME": str(root / "data"),
            "XDG_STATE_HOME": str(root / "state"),
            "OPENCODE_CONFIG": str(overlay),
            "OPENCODE_DISABLE_PROJECT_CONFIG": "true",
            "OPENCODE_DISABLE_CLAUDE_CODE": "true",
            "OPENCODE_DISABLE_MODELS_FETCH": "true",
            "OPENCODE_DISABLE_AUTOUPDATE": "true",
        }
        with native_server(executable, environment, root) as server:
            entries = server.request("/api/config", location=True)
            documents = [
                entry["info"] for entry in entries if entry["type"] == "document"
            ]
            declared = documents[0]
            assert declared["model"] == {
                "providerID": "opencode",
                "model": "big-pickle",
            }
            assert declared["permissions"] == global_configuration["permissions"]
            skills = server.request("/api/skill", location=True)["data"]
            expected_skills = {
                path.parent.name
                for directory in emitted_configuration["skills"]["paths"]
                for path in Path(directory).glob("*/SKILL.md")
            }
            assert expected_skills <= {skill["id"] for skill in skills}
            instructions = [
                item
                for document in documents
                for item in document.get("instructions", [])
            ]
            assert instructions == global_configuration["instructions"] + [
                "native-configuration-overlay.md"
            ]
            mcp_documents = [
                document["mcp"]["servers"]
                for document in documents
                if "mcp" in document
            ]
            merged_servers = {}
            for servers in mcp_documents:
                for name, settings in servers.items():
                    merged_servers.setdefault(name, {}).update(settings)
            assert merged_servers.keys() == emitted_configuration["mcp"].keys()
            for name, settings in merged_servers.items():
                assert settings["disabled"] is True
                if name in expected_timeouts:
                    assert settings["timeout"] == {
                        "catalog": expected_timeouts[name],
                        "execution": expected_timeouts[name],
                    }
                else:
                    assert "timeout" not in settings
                assert (
                    settings["command"] == emitted_configuration["mcp"][name]["command"]
                )
                assert (
                    settings["environment"]
                    == emitted_configuration["mcp"][name]["environment"]
                )


if __name__ == "__main__":
    verify_configuration(sys.argv[1], *map(Path, sys.argv[2:]))
