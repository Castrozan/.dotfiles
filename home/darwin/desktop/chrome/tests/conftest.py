import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

try:
    import psutil  # noqa: F401
except ModuleNotFoundError:
    psutil_stub = MagicMock()
    psutil_stub.NoSuchProcess = type("NoSuchProcess", (Exception,), {})
    psutil_stub.AccessDenied = type("AccessDenied", (Exception,), {})
    sys.modules["psutil"] = psutil_stub

SCRIPTS_DIRECTORY = Path(__file__).parent.parent / "scripts"
VERSION_DRIFT_RESTARTER_SCRIPTS_DIRECTORY = (
    SCRIPTS_DIRECTORY / "chrome_global_version_drift_restarter"
)

sys.path.insert(0, str(VERSION_DRIFT_RESTARTER_SCRIPTS_DIRECTORY))


class FakeChromeProcess:
    def __init__(self, command_line=None, executable_path="", access_error=None):
        self._command_line = command_line if command_line is not None else []
        self._executable_path = executable_path
        self._access_error = access_error
        self.terminate_called = False
        self.kill_called = False

    def cmdline(self):
        if self._access_error is not None:
            raise self._access_error
        return self._command_line

    def exe(self):
        if self._access_error is not None:
            raise self._access_error
        return self._executable_path

    def terminate(self):
        self.terminate_called = True

    def kill(self):
        self.kill_called = True


@pytest.fixture
def fake_chrome_process():
    return FakeChromeProcess
