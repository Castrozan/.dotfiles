import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts" / "temporary_directory_cleanup"

sys.path.insert(0, str(SCRIPTS_DIR))
