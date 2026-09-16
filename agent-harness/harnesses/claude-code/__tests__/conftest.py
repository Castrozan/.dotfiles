import sys
from pathlib import Path

PLUGIN_DIRECTORY = Path(__file__).parent.parent / "plugins"

sys.path.insert(0, str(PLUGIN_DIRECTORY))
