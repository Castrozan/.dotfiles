import sys
from pathlib import Path

OPENCODE_SCRIPTS_DIRECTORY = Path(__file__).parent.parent / "scripts"

sys.path.insert(0, str(OPENCODE_SCRIPTS_DIRECTORY))
