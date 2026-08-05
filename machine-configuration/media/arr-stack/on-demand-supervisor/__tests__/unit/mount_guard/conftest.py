import sys
from pathlib import Path

SUPERVISOR_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[3] / "scripts" / "on_demand_supervisor"
)
sys.path.insert(0, str(SUPERVISOR_PACKAGE_DIRECTORY_PATH))
