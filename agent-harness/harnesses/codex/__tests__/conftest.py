import sys
from pathlib import Path

CLAUDE_PLUGIN_PORT_DIRECTORY = Path(__file__).parent.parent / "claude-plugin-port"
PLUGIN_DISCOVERY_DIRECTORY = (
    Path(__file__).parent.parent.parent / "claude-code" / "plugin-discovery"
)

sys.path.insert(0, str(PLUGIN_DISCOVERY_DIRECTORY))
sys.path.insert(0, str(CLAUDE_PLUGIN_PORT_DIRECTORY))
