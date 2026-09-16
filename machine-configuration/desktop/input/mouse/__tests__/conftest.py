import sys
from pathlib import Path

SCRIPTS_DIRECTORY = Path(__file__).parent.parent / "scripts"

sys.path.insert(0, str(SCRIPTS_DIRECTORY))
