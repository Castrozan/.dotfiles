import sys
from pathlib import Path

workspace_profiles_directory = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(workspace_profiles_directory / "routing"))
