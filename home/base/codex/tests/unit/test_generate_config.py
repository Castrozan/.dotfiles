import os
import subprocess
import sys
import tomllib
from pathlib import Path


def test_generated_config_disables_welcome_tooltips(tmp_path):
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
        }
    )

    subprocess.run([sys.executable, str(generator_path)], check=True, env=env)

    generated_config = tomllib.loads((tmp_path / ".codex" / "config.toml").read_text())
    assert generated_config["tui"]["show_tooltips"] is False
