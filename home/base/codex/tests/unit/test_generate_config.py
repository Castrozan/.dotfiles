import os
import subprocess
import sys
import tomllib
from pathlib import Path


def generate_codex_config(tmp_path, env_overrides=None):
    generator_path = (
        Path(__file__).parent.parent.parent / "config-generator" / "generate_config.py"
    )
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(tmp_path),
            "CODEX_CHROME_DEVTOOLS_MCP_COMMAND": "chrome-mcp",
            "CODEX_CHROME_DEVTOOLS_MCP_ARGS_JSON": "[]",
            "CODEX_VIVALDI_DEVTOOLS_MCP_COMMAND": "vivaldi-mcp",
            "CODEX_VIVALDI_DEVTOOLS_MCP_ARGS_JSON": "[]",
        }
    )
    if env_overrides is not None:
        env.update(env_overrides)

    subprocess.run([sys.executable, str(generator_path)], check=True, env=env)

    return tomllib.loads((tmp_path / ".codex" / "config.toml").read_text())


def test_generated_config_disables_welcome_tooltips(tmp_path):
    generated_config = generate_codex_config(tmp_path)
    assert generated_config["tui"]["show_tooltips"] is False


def test_generated_config_defaults_to_full_bypass(tmp_path):
    generated_config = generate_codex_config(tmp_path)
    assert generated_config["sandbox_mode"] == "danger-full-access"
    assert generated_config["approval_policy"] == "never"


def test_generated_config_includes_vivaldi_devtools_when_command_present(tmp_path):
    generated_config = generate_codex_config(tmp_path)
    assert "vivaldi-devtools" in generated_config["mcp_servers"]


def test_generated_config_omits_vivaldi_devtools_when_command_empty(tmp_path):
    generated_config = generate_codex_config(
        tmp_path, {"CODEX_VIVALDI_DEVTOOLS_MCP_COMMAND": ""}
    )
    assert "vivaldi-devtools" not in generated_config["mcp_servers"]
    assert "chrome-devtools" in generated_config["mcp_servers"]


def test_generated_config_prunes_stale_vivaldi_devtools_entry(tmp_path):
    generate_codex_config(tmp_path)
    generated_config = generate_codex_config(
        tmp_path, {"CODEX_VIVALDI_DEVTOOLS_MCP_COMMAND": ""}
    )
    assert "vivaldi-devtools" not in generated_config["mcp_servers"]


def test_generated_config_never_emits_brave_devtools(tmp_path):
    generated_config = generate_codex_config(tmp_path)
    assert "brave-devtools" not in generated_config["mcp_servers"]
    assert "chrome-devtools" in generated_config["mcp_servers"]


def test_generated_config_prunes_stale_brave_devtools_entry(tmp_path):
    config_path = tmp_path / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        '[mcp_servers.brave-devtools]\ncommand = "brave-mcp"\nargs = []\n',
        encoding="utf-8",
    )
    generated_config = generate_codex_config(tmp_path)
    assert "brave-devtools" not in generated_config["mcp_servers"]
