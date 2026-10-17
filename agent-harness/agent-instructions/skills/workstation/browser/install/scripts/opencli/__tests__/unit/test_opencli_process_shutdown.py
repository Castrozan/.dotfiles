import importlib.util
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

specification = importlib.util.spec_from_file_location(
    "opencli_processes",
    Path(__file__).resolve().parents[2] / "opencli_processes.py",
)
module = importlib.util.module_from_spec(specification)
specification.loader.exec_module(module)


def test_exited_browser_with_no_signalable_group_members_is_clean(monkeypatch):
    process = Mock(pid=123)
    process.poll.return_value = 0
    monkeypatch.setattr(module.os, "killpg", Mock(side_effect=PermissionError))
    module.stop_process(process)


def test_live_browser_with_denied_forced_cleanup_reports_failure(monkeypatch):
    process = Mock(pid=123)
    process.poll.return_value = None
    process.wait.side_effect = subprocess.TimeoutExpired("browser", 5)
    monkeypatch.setattr(module.os, "killpg", Mock(side_effect=PermissionError))
    with pytest.raises(PermissionError):
        module.stop_process(process)
