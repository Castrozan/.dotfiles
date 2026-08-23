import sys
from pathlib import Path

SCRIPTS_DIRECTORY = Path(__file__).resolve().parent.parent / "scripts"

sys.path.insert(0, str(SCRIPTS_DIRECTORY))
sys.path.insert(0, str(SCRIPTS_DIRECTORY / "lib"))
