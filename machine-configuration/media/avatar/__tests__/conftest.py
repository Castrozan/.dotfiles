import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

scripts = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(scripts))
sys.path.insert(0, str(scripts / "listening"))
sys.path.insert(0, str(scripts / "echo"))
sys.path.insert(0, str(scripts / "conversation"))
sys.path.insert(0, str(scripts / "conversation" / "remote_seat"))
sys.path.insert(0, str(scripts / "wake"))
sys.path.insert(0, str(scripts / "live"))
agent_harness = Path(__file__).resolve().parents[4] / "agent-harness"
sys.path.append(str(agent_harness / "agent-to-agent-communication/client/scripts"))
sys.path.append(str(agent_harness / "servants"))
sys.path.append(str(agent_harness / "hooks/runtime/common"))


@pytest.fixture(autouse=True)
def no_meeting_seat_kept_on_this_machine(monkeypatch):
    monkeypatch.setattr("local_seat.meeting_seat_kept_here", Mock(return_value=False))
