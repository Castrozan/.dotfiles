import sys
from pathlib import Path

WORKAROUNDS_DIRECTORY = Path(__file__).parent.parent

sys.path.insert(0, str(WORKAROUNDS_DIRECTORY))
