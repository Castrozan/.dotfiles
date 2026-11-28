import sys
from pathlib import Path

SKILL_DIRECTORY = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(SKILL_DIRECTORY / "scripts" / "transcript_token_analysis"))
