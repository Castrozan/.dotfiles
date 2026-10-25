import subprocess
from unittest.mock import Mock

import pytest

import chatgpt_resource_scope as resource_scope
from chatgpt_processes import ProcessIdentity
from chatgpt_resource_scope import ChatGPTResourceScope


@pytest.fixture
def scope_fixture(monkeypatch):
    unit_name = "app-chatgpt-test.scope"
    target = f"/user.slice/app.slice/{unit_name}"
    primary = ProcessIdentity(42, 100)
    renderer = ProcessIdentity(43, 101)
    groups = {42: "/escaped.scope", 43: "/session.scope"}
    identities = {42: primary, 43: renderer}
    monkeypatch.setattr(
        resource_scope,
        "process_cgroup",
        lambda process_id: groups.get(process_id, target),
    )
    monkeypatch.setattr(ProcessIdentity, "read", staticmethod(identities.get))
    monkeypatch.setattr(
        resource_scope, "process_tree", lambda root: {primary, renderer}
    )
    monkeypatch.setattr(
        resource_scope,
        "is_primary_chatgpt_process",
        lambda identity: identity == primary,
    )
    command = Mock()
    monkeypatch.setattr(resource_scope.subprocess, "run", command)
    scope = ChatGPTResourceScope(unit_name)
    return scope, groups, identities, command, target


def test_chromium_main_and_renderers_are_attached_together(scope_fixture):
    scope, groups, _, command, target = scope_fixture

    def attach(arguments, **kwargs):
        assert arguments[6:9] == ["AttachProcessesToUnit", "ssau", scope.unit_name]
        assert set(arguments[-2:]) == {"42", "43"}
        groups.update({42: target, 43: target})

    command.side_effect = attach
    assert scope.repair_chromium_scope_migration(40)


def test_partial_attachment_is_retried_after_main_returns(scope_fixture):
    scope, groups, _, command, target = scope_fixture

    def attach(arguments, **kwargs):
        groups[42] = target
        if command.call_count == 1:
            raise subprocess.CalledProcessError(1, arguments)
        groups[43] = target

    command.side_effect = attach
    with pytest.raises(subprocess.CalledProcessError):
        scope.repair_chromium_scope_migration(40)
    assert scope.repair_chromium_scope_migration(40)
    assert command.call_count == 2


def test_recycled_process_id_is_excluded(scope_fixture):
    scope, groups, identities, command, target = scope_fixture
    identities[43] = ProcessIdentity(43, 999)

    def attach(arguments, **kwargs):
        assert arguments[-2:] == ["1", "42"]
        groups[42] = target

    command.side_effect = attach
    assert scope.repair_chromium_scope_migration(40)


def test_stable_scope_does_not_rewalk_process_tree(scope_fixture, monkeypatch):
    scope, groups, _, command, target = scope_fixture
    scope.primary_process = ProcessIdentity(42, 100)
    groups.update({42: target, 43: target})
    tree = Mock(
        side_effect=AssertionError("Stable membership must not rescan the tree")
    )
    monkeypatch.setattr(resource_scope, "process_tree", tree)
    assert scope.repair_chromium_scope_migration(40)
    command.assert_not_called()


def test_attachment_audit_finds_a_child_created_during_migration(
    scope_fixture, monkeypatch
):
    scope, groups, identities, command, target = scope_fixture
    primary = identities[42]
    renderer = identities[43]
    monkeypatch.setattr(
        resource_scope,
        "process_tree",
        lambda root: {primary} if groups[42] != target else {primary, renderer},
    )

    def attach(arguments, **kwargs):
        for value in arguments[11:]:
            groups[int(value)] = target

    command.side_effect = attach
    assert scope.repair_chromium_scope_migration(40)
    assert groups[43] != target
    assert scope.repair_chromium_scope_migration(40)
    assert groups[43] == target
    assert command.call_count == 2


@pytest.fixture
def signal_capture(monkeypatch):
    monkeypatch.setattr(
        resource_scope.os,
        "pidfd_open",
        lambda process_id: process_id + 1000,
        raising=False,
    )
    monkeypatch.setattr(resource_scope.os, "close", Mock())
    signalled = Mock()
    monkeypatch.setattr(
        resource_scope.signal, "pidfd_send_signal", signalled, raising=False
    )
    return signalled


def test_quit_terminates_only_the_verified_primary_process(
    scope_fixture, signal_capture
):
    scope, _, _, _, _ = scope_fixture
    scope.primary_process = ProcessIdentity(42, 100)
    scope.quit_app()
    signal_capture.assert_called_once_with(1042, resource_scope.signal.SIGTERM)


def test_quit_spares_a_recycled_primary_process_id(scope_fixture, signal_capture):
    scope, _, identities, _, _ = scope_fixture
    scope.primary_process = ProcessIdentity(42, 100)
    identities[42] = ProcessIdentity(42, 999)
    scope.quit_app()
    signal_capture.assert_not_called()


def test_quit_without_a_known_primary_process_signals_nothing(
    scope_fixture, signal_capture
):
    scope, _, _, _, _ = scope_fixture
    scope.quit_app()
    signal_capture.assert_not_called()


def test_cleanup_excludes_controller_and_processes_outside_the_scope(
    scope_fixture, monkeypatch
):
    scope, groups, _, _, target = scope_fixture
    groups[42] = target
    monkeypatch.setattr(scope, "process_ids", lambda: {99, 42, 43})
    monkeypatch.setattr(resource_scope.os, "getpid", lambda: 99)
    monkeypatch.setattr(
        resource_scope.os,
        "pidfd_open",
        lambda process_id: process_id + 1000,
        raising=False,
    )
    closed = Mock()
    signalled = Mock()
    monkeypatch.setattr(resource_scope.os, "close", closed)
    monkeypatch.setattr(
        resource_scope.signal, "pidfd_send_signal", signalled, raising=False
    )
    scope.terminate_remaining_helpers()
    signalled.assert_called_once_with(1042, resource_scope.signal.SIGTERM)
    assert {call.args[0] for call in closed.call_args_list} == {1042, 1043}
