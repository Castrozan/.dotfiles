import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[2]
        / "agent-harness"
        / "measurement-and-reporting"
        / "snapshot-ingestion"
    ),
)
