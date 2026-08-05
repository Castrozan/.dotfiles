import sys
from pathlib import Path

A2A_CLI_PACKAGE_PARENT_DIRECTORY = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(A2A_CLI_PACKAGE_PARENT_DIRECTORY))
