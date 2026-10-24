from unittest.mock import Mock

import pytest

import chatgpt_resource_control as resource_control


def run_controlled_app(monkeypatch, window_states_after_each_poll, scope=None):
    scope = scope or Mock()
    scope.repair_chromium_scope_migration.return_value = True
    scope.process_ids.return_value = {42}
    observer = Mock(refresh_needed=False, window_open=True)
    elapsed = [0]
    remaining_states = list(window_states_after_each_poll)

    def advance(timeout_seconds):
        elapsed[0], observer.window_open = remaining_states.pop(0)

    observer.poll.side_effect = advance
    child = Mock(pid=42, returncode=0)
    child.poll.side_effect = [None] * len(remaining_states) + [0]
    launch = Mock(return_value=child)
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
    return scope, child


def test_closing_the_window_quits_the_app_once_after_the_grace(monkeypatch):
    scope, child = run_controlled_app(
        monkeypatch, [(40, False), (44, False), (46, False), (47, False), (48, False)]
    )
    scope.quit_app.assert_called_once_with()
    child.kill.assert_not_called()
    scope.terminate_remaining_helpers.assert_called_once_with()


def test_a_window_reopened_within_the_grace_keeps_the_app(monkeypatch):
    scope, _ = run_controlled_app(
        monkeypatch, [(40, False), (43, True), (44, False), (48, False), (49, False)]
    )
    scope.quit_app.assert_not_called()


def test_a_window_closed_during_startup_waits_for_the_headroom(monkeypatch):
    scope, _ = run_controlled_app(
        monkeypatch, [(5, False), (20, False), (29, False), (30, False)]
    )
    scope.quit_app.assert_not_called()


def test_failed_grouping_never_quits(monkeypatch):
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
    scope.quit_app.assert_not_called()


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
    scope.quit_app.assert_not_called()
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


def test_resource_and_desktop_failures_keep_the_app_running(monkeypatch):
    scope = Mock()
    scope.repair_chromium_scope_migration.side_effect = [OSError(), True]
    observer = Mock(refresh_needed=False, window_open=False)
    observer.poll.side_effect = [ValueError(), None]
    child = Mock(pid=42, returncode=0)
    child.poll.side_effect = [None, None, 0]
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
    scope.quit_app.assert_not_called()
    child.terminate.assert_not_called()
    child.kill.assert_not_called()
    assert observer.disconnect.call_count == 2
