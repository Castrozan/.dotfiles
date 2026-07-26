import sys
from pathlib import Path

USAGE_SCRIPT_DIRECTORY = Path(__file__).resolve().parent.parent
INGESTION_SCRIPT_DIRECTORY = USAGE_SCRIPT_DIRECTORY.parent.parent / "ingestion"

sys.path.insert(0, str(USAGE_SCRIPT_DIRECTORY))
sys.path.insert(0, str(INGESTION_SCRIPT_DIRECTORY))
