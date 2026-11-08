import sys
from pathlib import Path

VOICE_SCRIPTS_DIRECTORY = Path(__file__).parent.parent / "scripts"

sys.path.insert(0, str(VOICE_SCRIPTS_DIRECTORY))
