import importlib.machinery
import importlib.util
import os
import subprocess
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


@pytest.fixture(scope="module")
def daemon(monkeypatch_module_scope):
    for module_name, module_stub in build_cocoa_module_stubs().items():
        monkeypatch_module_scope.setitem(sys.modules, module_name, module_stub)
    loader = importlib.machinery.SourceFileLoader(
        "quit_windowless_applications_daemon", str(DAEMON_SOURCE_PATH)
    )
    specification = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(specification)
    loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def monkeypatch_module_scope():
    monkeypatch = pytest.MonkeyPatch()
    yield monkeypatch
    monkeypatch.undo()


def test_application_keeps_running_while_its_window_is_still_open(daemon):
    history = daemon.ApplicationWindowHistory(
        first_seen_at=0.0, last_seen_with_a_window_at=100.0
    )

    assert not daemon.should_request_quit(history, 100.0)


def test_application_is_quit_once_its_last_window_closes(daemon):
    history = daemon.ApplicationWindowHistory(
        first_seen_at=0.0, last_seen_with_a_window_at=100.0
    )
    still_within_grace = 100.0 + daemon.SECONDS_WITHOUT_A_WINDOW_BEFORE_QUITTING - 1
    past_grace = 100.0 + daemon.SECONDS_WITHOUT_A_WINDOW_BEFORE_QUITTING

    assert not daemon.should_request_quit(history, still_within_grace)
    assert daemon.should_request_quit(history, past_grace)


def test_application_that_never_opened_a_window_is_still_quit(daemon):
    history = daemon.ApplicationWindowHistory(first_seen_at=0.0)
    launch_grace = daemon.SECONDS_AFTER_LAUNCH_BEFORE_QUITTING_AN_APPLICATION_THAT_NEVER_OPENED_A_WINDOW

    assert not daemon.should_request_quit(history, launch_grace - 1)
    assert daemon.should_request_quit(history, launch_grace)


def test_quit_is_requested_again_when_the_application_ignores_the_first_request(daemon):
    history = daemon.ApplicationWindowHistory(
        first_seen_at=0.0, last_seen_with_a_window_at=100.0, quit_requested_at=110.0
    )
    repeat_interval = daemon.SECONDS_BETWEEN_REPEATED_QUIT_REQUESTS

    assert not daemon.should_request_quit(history, 110.0 + repeat_interval - 1)
    assert daemon.should_request_quit(history, 110.0 + repeat_interval)


def test_an_application_whose_process_already_exited_is_not_reported_as_running(
    daemon, monkeypatch
):
    already_exited_process = subprocess.Popen(["/bin/sh", "-c", "exit 0"])
    already_exited_process.wait()
    running_process_identifier = os.getpid()
    workspace_entries = [
        types.SimpleNamespace(
            processIdentifier=lambda: running_process_identifier,
            activationPolicy=lambda: daemon.NSApplicationActivationPolicyRegular,
        ),
        types.SimpleNamespace(
            processIdentifier=lambda: already_exited_process.pid,
            activationPolicy=lambda: daemon.NSApplicationActivationPolicyRegular,
        ),
    ]
    monkeypatch.setattr(
        daemon,
        "NSWorkspace",
        types.SimpleNamespace(
            sharedWorkspace=lambda: types.SimpleNamespace(
                runningApplications=lambda: workspace_entries
            )
        ),
    )

    still_running = daemon.get_running_regular_applications()

    assert [entry.processIdentifier() for entry in still_running] == [
        running_process_identifier
    ]


def test_history_of_applications_that_exited_is_discarded(daemon):
    window_history_by_process_identifier = {
        101: daemon.ApplicationWindowHistory(first_seen_at=0.0),
        202: daemon.ApplicationWindowHistory(first_seen_at=0.0),
    }
    still_running_applications = [
        types.SimpleNamespace(processIdentifier=lambda: 101),
    ]

    daemon.forget_applications_that_exited(
        window_history_by_process_identifier, still_running_applications
    )

    assert list(window_history_by_process_identifier) == [101]
