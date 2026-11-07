import sys
from pathlib import Path

EVALUATIONS_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(EVALUATIONS_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent / "unit"))
