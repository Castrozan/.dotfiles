import sys
from pathlib import Path

cycle_directory = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(cycle_directory / "scripts"))
sys.path.insert(0, str(cycle_directory.parent))
