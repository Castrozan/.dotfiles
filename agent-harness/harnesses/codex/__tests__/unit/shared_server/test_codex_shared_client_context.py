import json
import os
from uuid import uuid4

import pytest

from codex_client_context import (
    ClientContext,
    ContextConflict,
    read_context,
    restore_hook_context,
)


def test_exclusive_attachment_rejects_another_client_until_release(tmp_path):
    thread = str(uuid4())
    first = ClientContext(tmp_path, {"HERDR_PANE_ID": "first"})
    second = ClientContext(tmp_path, {"HERDR_PANE_ID": "second"})
    first.claim(thread)
    try:
        with pytest.raises(ContextConflict):
            second.claim(thread)
        assert read_context(tmp_path, thread)["environment"] == {
            "HERDR_PANE_ID": "first"
        }
    finally:
        first.close()
    second.claim(thread)
    try:
        assert read_context(tmp_path, thread)["environment"] == {
            "HERDR_PANE_ID": "second"
        }
    finally:
        second.close()
    assert read_context(tmp_path, thread) is None


def test_stale_context_is_not_trusted_without_an_owner_lock(tmp_path):
    thread = str(uuid4())
    (tmp_path / f"{thread}.json").write_text(json.dumps({"HERDR_PANE_ID": "stale"}))
    assert read_context(tmp_path, thread) is None


def test_context_never_persists_unrelated_environment(tmp_path):
    thread = str(uuid4())
    context = ClientContext(
        tmp_path, {"HERDR_PANE_ID": "first", "SECRET_TOKEN": "secret"}
    )
    context.claim(thread)
    try:
        assert "secret" not in (tmp_path / f"{thread}.json").read_text()
        assert (tmp_path / f"{thread}.json").stat().st_mode & 0o777 == 0o600
    finally:
        context.close()


def test_shared_hook_restores_only_its_session_and_clears_stale_markers(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    monkeypatch.setenv("DOTFILES_CODEX_SHARED_SERVER", "1")
    monkeypatch.setenv("HERDR_PANE_ID", "wrong")
    monkeypatch.setenv("CLAWDE_AGENT_NAME", "wrong")
    thread = str(uuid4())
    context = ClientContext(tmp_path / "client-context", {"HERDR_PANE_ID": "correct"})
    context.claim(thread)
    try:
        restore_hook_context({"session_id": thread})
        assert os.environ["HERDR_PANE_ID"] == "correct"
        assert "CLAWDE_AGENT_NAME" not in os.environ
        restore_hook_context({"session_id": str(uuid4())})
        assert "HERDR_PANE_ID" not in os.environ
    finally:
        context.close()


def test_embedded_hooks_keep_their_inherited_context(monkeypatch):
    monkeypatch.delenv("DOTFILES_CODEX_SHARED_SERVER", raising=False)
    monkeypatch.setenv("HERDR_PANE_ID", "embedded")
    restore_hook_context({"session_id": str(uuid4())})
    assert os.environ["HERDR_PANE_ID"] == "embedded"


def test_reconnect_fingerprint_does_not_make_a_disconnected_context_active(tmp_path):
    identifier = str(uuid4())
    first = ClientContext(tmp_path, {"HERDR_PANE_ID": "first", "PATH": "original"})
    first.claim(identifier)
    first.close()
    same = ClientContext(tmp_path, {"HERDR_PANE_ID": "first", "PATH": "original"})
    changed = ClientContext(tmp_path, {"HERDR_PANE_ID": "first", "PATH": "new"})
    assert same.matches_configuration(identifier)
    assert not changed.matches_configuration(identifier)
    assert read_context(tmp_path, identifier) is None


def test_reserving_a_previous_thread_does_not_activate_its_stale_pane(tmp_path):
    identifier = str(uuid4())
    first = ClientContext(tmp_path, {"HERDR_PANE_ID": "first"})
    first.claim(identifier)
    first.close()
    second = ClientContext(tmp_path, {"HERDR_PANE_ID": "second"})
    second.reserve(identifier)
    try:
        assert read_context(tmp_path, identifier) is None
        second.claim(identifier)
        assert (
            read_context(tmp_path, identifier)["environment"]["HERDR_PANE_ID"]
            == "second"
        )
    finally:
        second.close()


@pytest.mark.parametrize("thread", ["../outside", "", None])
def test_invalid_thread_identifiers_cannot_address_context_files(tmp_path, thread):
    assert read_context(tmp_path, thread) is None
