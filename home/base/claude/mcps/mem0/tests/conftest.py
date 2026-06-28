import sys
from pathlib import Path

MEM0_MCP_SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(MEM0_MCP_SCRIPTS_DIRECTORY))
