import sys
from pathlib import Path

scripts_directory = Path(__file__).resolve().parents[2] / "scripts"
if str(scripts_directory) not in sys.path:
    sys.path.insert(0, str(scripts_directory))
