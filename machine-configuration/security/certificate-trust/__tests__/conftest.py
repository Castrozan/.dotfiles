import sys
from pathlib import Path

CERTIFICATE_TRUST_SCRIPTS_DIRECTORY = Path(__file__).parent.parent / "scripts"

sys.path.insert(0, str(CERTIFICATE_TRUST_SCRIPTS_DIRECTORY))
