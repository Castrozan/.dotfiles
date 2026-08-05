import sys
from pathlib import Path

AGENTS_DIRECTORY_PATH = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AGENTS_DIRECTORY_PATH))
