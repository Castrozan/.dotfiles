from unittest.mock import Mock

import pytest

import chatgpt_resource_control as resource_control
from chatgpt_memory_policy import (
    BACKGROUND_MEMORY_HIGH_BYTES,
    OPEN_WINDOW_MEMORY_HIGH_BYTES,
)


def test_launch_arguments_and_window_transitions_preserve_the_running_app(monkeypatch):
    scope = Mock()
    scope.repair_chromium_scope_migration.return_value = True
    scope.process_ids.return_value = {42}
    observer = Mock()
    observer.refresh_needed = False
    observer.window_open = True
    child = Mock(pid=42, returncode=0)
    child.poll.side_effect = [None, None, None, 0]
    launch = Mock(return_value=child)
    elapsed = [0]

    def advance(timeout_seconds):
        elapsed[0] += 40
        observer.window_open = False if elapsed[0] == 40 else None

    observer.poll.side_effect = advance
    monkeypatch.setattr(
        resource_control, "ChatGPTResourceScope", Mock(return_value=scope)
    )
    monkeypatch.setattr(
        resource_control, "ChatGPTWindowObserver", Mock(return_value=observer)
    )
    monkeypatch.setattr(resource_control.subprocess, "Popen", launch)
    monkeypatch.setattr(resource_control.time, "monotonic", lambda: elapsed[0])
    command = [
        "/runtime/chatgpt",
        "chatgpt://auth?code=fixture&literal=$value",
        "space in argument",
    ]
    assert resource_control.control_app("app-chatgpt-test.scope", command) == 0
    launch.assert_called_once_with(command)
    assert [call.args[0] for call in scope.set_memory_high.call_args_list] == [
        OPEN_WINDOW_MEMORY_HIGH_BYTES,
        BACKGROUND_MEMORY_HIGH_BYTES,
        OPEN_WINDOW_MEMORY_HIGH_BYTES,
    ]
    child.terminate.assert_not_called()
    child.kill.assert_not_called()
    scope.terminate_remaining_helpers.assert_called_once_with()


def test_failed_grouping_keeps_open_headroom(monkeypatch):
    scope = Mock()
    scope.repair_chromium_scope_migration.return_value = False
    observer = Mock(refresh_needed=False, window_open=False)
    child = Mock(pid=42, returncode=0)
    child.poll.side_effect = [None, 0]
    monkeypatch.setattr(
        resource_control, "ChatGPTResourceScope", Mock(return_value=scope)
    )
    monkeypatch.setattr(
        resource_control, "ChatGPTWindowObserver", Mock(return_value=observer)
    )
    monkeypatch.setattr(resource_control.subprocess, "Popen", Mock(return_value=child))
    monkeypatch.setattr(resource_control.time, "monotonic", Mock(side_effect=[0, 90]))
    assert (
        resource_control.control_app("app-chatgpt-test.scope", ["/runtime/chatgpt"])
        == 0
    )
    scope.set_memory_high.assert_called_once_with(OPEN_WINDOW_MEMORY_HIGH_BYTES)


def test_attachment_preserves_the_existing_process_and_tool_helpers(monkeypatch):
    identity = resource_control.ProcessIdentity(42, 100)
    scope = Mock()
    scope.repair_chromium_scope_migration.return_value = True
    observer = Mock(refresh_needed=False, window_open=True)
    launch = Mock()
    monkeypatch.setattr(
        resource_control, "ChatGPTResourceScope", Mock(return_value=scope)
    )
    monkeypatch.setattr(
        resource_control, "ChatGPTWindowObserver", Mock(return_value=observer)
    )
    monkeypatch.setattr(
        resource_control, "is_primary_chatgpt_process", lambda value: value == identity
    )
    monkeypatch.setattr(
        resource_control.ProcessIdentity,
        "read",
        Mock(side_effect=[identity, identity, None]),
    )
    monkeypatch.setattr(resource_control.subprocess, "Popen", launch)
    assert resource_control.attach_running_app("app-chatgpt-test.scope", 42) == 0
    scope.repair_chromium_scope_migration.assert_called_once_with(42)
    scope.set_memory_high.assert_called_once_with(OPEN_WINDOW_MEMORY_HIGH_BYTES)
    scope.terminate_remaining_helpers.assert_not_called()
    launch.assert_not_called()


def test_attachment_rejects_an_unrelated_process(monkeypatch):
    monkeypatch.setattr(
        resource_control.ProcessIdentity,
        "read",
        Mock(return_value=resource_control.ProcessIdentity(42, 100)),
    )
    monkeypatch.setattr(
        resource_control, "is_primary_chatgpt_process", Mock(return_value=False)
    )
    scope = Mock()
    monkeypatch.setattr(resource_control, "ChatGPTResourceScope", scope)
    with pytest.raises(ValueError, match="ChatGPT main process"):
        resource_control.attach_running_app("app-chatgpt-test.scope", 42)
    scope.assert_not_called()
