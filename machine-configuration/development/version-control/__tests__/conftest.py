import sys
from pathlib import Path

version_control_directory = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(version_control_directory / "scripts"))
