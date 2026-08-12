import sys
from pathlib import Path

PLUGIN_DISCOVERY_DIRECTORY = Path(__file__).parent.parent / "plugin-discovery"

sys.path.insert(0, str(PLUGIN_DISCOVERY_DIRECTORY))
