import importlib.machinery
import importlib.util
import sys
import types
from pathlib import Path

import pytest

DAEMON_SOURCE_PATH = (
    Path(__file__).resolve().parents[2] / "quit-windowless-applications-daemon"
)


def build_cocoa_module_stubs():
    quartz_stub = types.ModuleType("Quartz")
    quartz_stub.CGWindowListCopyWindowInfo = lambda *_arguments: []
    quartz_stub.kCGWindowListOptionAll = 0
    quartz_stub.kCGWindowListExcludeDesktopElements = 0
    quartz_stub.kCGNullWindowID = 0
    quartz_stub.kCGWindowLayer = "kCGWindowLayer"
    quartz_stub.kCGWindowBounds = "kCGWindowBounds"
    quartz_stub.kCGWindowOwnerPID = "kCGWindowOwnerPID"

    appkit_stub = types.ModuleType("AppKit")
    appkit_stub.NSApplicationActivationPolicyRegular = 0
    appkit_stub.NSWorkspace = types.SimpleNamespace(sharedWorkspace=lambda: None)
    appkit_stub.NSScreen = types.SimpleNamespace(screens=lambda: [])

    foundation_stub = types.ModuleType("Foundation")
    foundation_stub.NSDate = types.SimpleNamespace(
        dateWithTimeIntervalSinceNow_=lambda _seconds: None
    )
    foundation_stub.NSRunLoop = types.SimpleNamespace(
        currentRunLoop=lambda: types.SimpleNamespace(runUntilDate_=lambda _date: None)
    )

    return {
        "Quartz": quartz_stub,
        "AppKit": appkit_stub,
        "Foundation": foundation_stub,
    }


@pytest.fixture(scope="session")
def cocoa_module_stub_patcher():
    monkeypatch = pytest.MonkeyPatch()
    yield monkeypatch
    monkeypatch.undo()


@pytest.fixture(scope="session")
def daemon(cocoa_module_stub_patcher):
    for module_name, module_stub in build_cocoa_module_stubs().items():
        cocoa_module_stub_patcher.setitem(sys.modules, module_name, module_stub)
    loader = importlib.machinery.SourceFileLoader(
        "quit_windowless_applications_daemon", str(DAEMON_SOURCE_PATH)
    )
    specification = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(specification)
    loader.exec_module(module)
    return module


def build_screen(origin_x, origin_y, height, visible_height=None):
    return types.SimpleNamespace(
        frame=lambda: types.SimpleNamespace(
            origin=types.SimpleNamespace(x=origin_x, y=origin_y),
            size=types.SimpleNamespace(height=height),
        ),
        visibleFrame=lambda: types.SimpleNamespace(
            origin=types.SimpleNamespace(x=origin_x, y=origin_y),
            size=types.SimpleNamespace(height=visible_height),
        ),
    )
