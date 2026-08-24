import sys
from pathlib import Path

HEY_BOT_PYTHON_PATH = Path(__file__).parent.parent / "scripts"

sys.path.insert(0, str(HEY_BOT_PYTHON_PATH))
