import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
agent_harness = Path(__file__).resolve().parents[5]
sys.path.extend(
    str(agent_harness / directory)
    for directory in (
        "agent-to-agent-communication/client/scripts",
        "servants",
        "hooks/runtime/common",
    )
)
