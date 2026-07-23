import sys
from pathlib import Path

CLAUDE_PLUGIN_PORT_DIRECTORY = Path(__file__).parent.parent / "claude-plugin-port"

sys.path.insert(0, str(CLAUDE_PLUGIN_PORT_DIRECTORY))
