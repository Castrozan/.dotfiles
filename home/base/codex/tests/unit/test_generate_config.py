import os
import subprocess
import sys
import tomllib
from pathlib import Path


def generate_codex_config(tmp_path):
    generator_path = (
        Path(__file__).parent.parent.parent / "config-generator" / "generate_config.py"
    )
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(tmp_path),
            "CODEX_CHROME_DEVTOOLS_MCP_COMMAND": "chrome-mcp",
            "CODEX_CHROME_DEVTOOLS_MCP_ARGS_JSON": "[]",
            "CODEX_BRAVE_DEVTOOLS_MCP_COMMAND": "brave-mcp",
            "CODEX_BRAVE_DEVTOOLS_MCP_ARGS_JSON": "[]",
            "CODEX_VIVALDI_DEVTOOLS_MCP_COMMAND": "vivaldi-mcp",
            "CODEX_VIVALDI_DEVTOOLS_MCP_ARGS_JSON": "[]",
        }
    )

    subprocess.run([sys.executable, str(generator_path)], check=True, env=env)

    return tomllib.loads((tmp_path / ".codex" / "config.toml").read_text())


def test_generated_config_disables_welcome_tooltips(tmp_path):
    generated_config = generate_codex_config(tmp_path)
    assert generated_config["tui"]["show_tooltips"] is False


def test_generated_config_defaults_to_full_bypass(tmp_path):
    generated_config = generate_codex_config(tmp_path)
    assert generated_config["sandbox_mode"] == "danger-full-access"
    assert generated_config["approval_policy"] == "never"
