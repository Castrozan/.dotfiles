import importlib.machinery
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIRECTORY = Path(__file__).resolve().parent.parent
SEED_CONFIG_DIR_OVERLAY_SCRIPT_PATH = (
    SCRIPTS_DIRECTORY / "seed-claude-config-dir-overlay"
)


def import_extensionless_python_script(extensionless_name):
    script_path = SCRIPTS_DIRECTORY / extensionless_name
    module_name = extensionless_name.replace("-", "_")
    loader = importlib.machinery.SourceFileLoader(module_name, str(script_path))
    spec = importlib.util.spec_from_loader(module_name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module


import_extensionless_python_script("merge-discord-agent-access")


@pytest.fixture
def shared_config_directory(tmp_path):
    home = tmp_path / "home"
    shared = home / ".claude"
    (shared / "skills" / "git").mkdir(parents=True)
    (shared / "skills" / "git" / "SKILL.md").write_text("shared skill body")
    (shared / "plugins").mkdir()
    (shared / "plugins" / "shared-plugin.json").write_text("{}")
    (shared / "CLAUDE.md").write_text("shared core rules")
    (shared / "settings.json").write_text(
        json.dumps(
            {
                "model": "opus",
                "theme": "dark",
                "voice": "off",
                "effortLevel": "high",
                "retiredSetting": True,
            }
        )
    )
    (home / ".claude.json").write_text(
        json.dumps(
            {
                "installMethod": "shared",
                "mcpServers": {"chrome-devtools": {"command": "chrome-devtools-mcp"}},
            }
        )
    )
    return shared


@pytest.fixture
def seed_config_dir_overlay_script_path():
    return SEED_CONFIG_DIR_OVERLAY_SCRIPT_PATH


@pytest.fixture
def settings_overlay_file(tmp_path):
    overlay_path = tmp_path / "overlay.json"
    overlay_path.write_text(
        json.dumps({"model": "sonnet", "enabledPlugins": {"work": True}})
    )
    return overlay_path


@pytest.fixture
def run_seed(tmp_path, shared_config_directory, settings_overlay_file):
    isolated = tmp_path / "isolated-config"

    def invoke() -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(SEED_CONFIG_DIR_OVERLAY_SCRIPT_PATH),
                "--source-config-directory",
                str(shared_config_directory),
                "--target-config-directory",
                str(isolated),
                "--settings-overlay-file",
                str(settings_overlay_file),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

    return invoke, isolated
