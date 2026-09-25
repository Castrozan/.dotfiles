import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def verify_configuration(executable, settings, plugin_settings, bundle):
    global_configuration = json.loads(settings.read_text())
    emitted_configuration = json.loads(
        (bundle / ".opencode/opencode.jsonc").read_text()
    )
    installed_configuration = json.loads(plugin_settings.read_text())
    expected_timeouts = {
        "plugin.dotfiles.chrome-devtools": 120000,
        "plugin.dotfiles.sonarqube": 60000,
    }
    assert "mcp" not in global_configuration
    assert "skills" not in global_configuration
    for name, timeout in expected_timeouts.items():
        assert installed_configuration["mcp"][name].pop("timeout") == timeout
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
                        name: {"enabled": False}
                        for name in emitted_configuration["mcp"]
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
        result = subprocess.run(
            [executable, "debug", "config"],
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        effective = json.loads(result.stdout)
        assert effective["model"] == global_configuration["model"]
        assert effective["permission"] == global_configuration["permission"]
        assert effective["skills"] == emitted_configuration["skills"]
        assert effective["instructions"] == global_configuration["instructions"] + [
            "native-configuration-overlay.md"
        ]
        assert effective["mcp"].keys() == emitted_configuration["mcp"].keys()
        for name, server in effective["mcp"].items():
            assert server["enabled"] is False
            assert server["timeout"] == expected_timeouts[name]
            assert server["command"] == emitted_configuration["mcp"][name]["command"]
            assert (
                server["environment"]
                == emitted_configuration["mcp"][name]["environment"]
            )


if __name__ == "__main__":
    verify_configuration(sys.argv[1], *map(Path, sys.argv[2:]))
