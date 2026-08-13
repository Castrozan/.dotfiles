import sys
from pathlib import Path

PLUGIN_DISCOVERY_DIRECTORY = Path(__file__).parent.parent / "plugin-discovery"
PLUGIN_UPDATES_DIRECTORY = Path(__file__).parent.parent / "plugin-updates"

sys.path.insert(0, str(PLUGIN_DISCOVERY_DIRECTORY))
sys.path.insert(0, str(PLUGIN_UPDATES_DIRECTORY))
