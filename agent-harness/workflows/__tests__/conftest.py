import sys
from pathlib import Path

WORKFLOWS_DIRECTORY = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(WORKFLOWS_DIRECTORY / "scripts"))
sys.path.insert(
    0, str(WORKFLOWS_DIRECTORY / "definitions/dotfiles-housekeeping/scripts")
)
