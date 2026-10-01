import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
LIB_DIR = SCRIPTS_DIR / "lib"

sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))
