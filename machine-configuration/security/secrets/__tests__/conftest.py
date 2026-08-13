import sys
from pathlib import Path

SECRETS_SCRIPTS_DIRECTORY = Path(__file__).parent.parent / "scripts"

sys.path.insert(0, str(SECRETS_SCRIPTS_DIRECTORY))
