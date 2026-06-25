import importlib.machinery
import importlib.util
import sys
import types
from pathlib import Path

import pytest

WATCHDOG_DIRECTORY = Path(__file__).resolve().parent.parent
WATCHDOG_SCRIPT_PATH = (
    WATCHDOG_DIRECTORY / "kill_runaway_chrome_devtools_mcp_instances.py"
)


class FakePsutilNoSuchProcess(Exception):
    pass


class FakePsutilAccessDenied(Exception):
    pass


class FakePsutilTimeoutExpired(Exception):
    pass


def build_fake_psutil_module():
    fake_psutil = types.ModuleType("psutil")
    fake_psutil.NoSuchProcess = FakePsutilNoSuchProcess
    fake_psutil.AccessDenied = FakePsutilAccessDenied
    fake_psutil.TimeoutExpired = FakePsutilTimeoutExpired
    fake_psutil.process_iter = lambda attributes=None: iter([])
    return fake_psutil


def import_watchdog_module_with_fake_psutil():
    sys.modules["psutil"] = build_fake_psutil_module()
    module_name = "kill_runaway_chrome_devtools_mcp_instances"
    loader = importlib.machinery.SourceFileLoader(
        module_name, str(WATCHDOG_SCRIPT_PATH)
    )
    spec = importlib.util.spec_from_loader(module_name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module


@pytest.fixture
def watchdog_module():
    return import_watchdog_module_with_fake_psutil()
