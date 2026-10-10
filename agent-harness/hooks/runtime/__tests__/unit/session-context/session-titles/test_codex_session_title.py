from unittest.mock import Mock

import pytest

from codex_app_server_client import CodexThreadTitle
import codex_session_title as title_command
import codex_servant_status_handler as status_handler
import servant_identity_handler


@pytest.fixture
def generated_title_client(session_client, monkeypatch):
    client, connection = session_client
    monkeypatch.setattr(title_command, "CodexAppServerClient", connection)
    thread_identifier = "generated-title-command"
    servant = servant_identity_handler.servant_for_hook_input(
        {"thread_id": thread_identifier}
    )
    preview = "Can you investigate why the terminal never shows a useful session name?"
    original = CodexThreadTitle(f"{servant['name']} | {preview}", preview)
    client.thread_title.return_value = original
    return client, connection, thread_identifier, servant, original


def test_generated_title_is_saved_with_plain_servant_prefix(
    generated_title_client, tmp_path
):
    client, connection, thread_identifier, servant, original = generated_title_client
    assert title_command.set_generated_session_title(
        thread_identifier, original.name_digest, "Restore useful session titles"
    )
    connection.assert_called_once_with(str(tmp_path / "private.sock"))
    client.set_thread_name.assert_called_once_with(
        thread_identifier, f"{servant['name']} | Restore useful session titles"
    )


def test_repeated_command_preserves_completed_title(generated_title_client):
    client, _, thread_identifier, servant, original = generated_title_client
    assert title_command.set_generated_session_title(
        thread_identifier, original.name_digest, "Restore useful session titles"
    )
    client.thread_title.return_value = CodexThreadTitle(
        f"{servant['name']} | Restore useful session titles", original.preview
    )
    assert not title_command.set_generated_session_title(
        thread_identifier, original.name_digest, "Rename again"
    )
    assert client.set_thread_name.call_count == 1


def test_generated_title_equal_to_preview_is_not_requested_again(
    generated_title_client,
):
    client, _, thread_identifier, servant, original = generated_title_client
    original = CodexThreadTitle(servant["name"], "Fix terminal title")
    client.thread_title.return_value = original
    assert title_command.set_generated_session_title(
        thread_identifier, original.name_digest, original.preview
    )
    client.thread_title.return_value = CodexThreadTitle(
        f"{servant['name']} | {original.preview}", original.preview
    )
    assert not title_command.set_generated_session_title(
        thread_identifier, client.thread_title.return_value.name_digest, "Rename again"
    )
    assert client.set_thread_name.call_count == 1
    assert (
        status_handler.handle(
            {"thread_id": thread_identifier, "hook_event_name": "UserPromptSubmit"}
        )
        is None
    )


def test_human_rename_after_hook_prevents_generated_overwrite(generated_title_client):
    client, _, thread_identifier, servant, original = generated_title_client
    client.thread_title.return_value = CodexThreadTitle(
        f"{servant['name']} | My investigation", original.preview
    )
    assert not title_command.set_generated_session_title(
        thread_identifier, original.name_digest, "Restore useful session titles"
    )
    client.set_thread_name.assert_not_called()


def test_custom_title_is_protected_even_with_matching_name_digest(
    generated_title_client,
):
    client, _, thread_identifier, servant, original = generated_title_client
    custom = CodexThreadTitle(f"{servant['name']} | My investigation", original.preview)
    client.thread_title.return_value = custom
    assert not title_command.set_generated_session_title(
        thread_identifier, custom.name_digest, "Restore useful session titles"
    )
    client.set_thread_name.assert_not_called()


@pytest.mark.parametrize(
    "task_title", ["", " \n\t", "x" * 81, "BB | Task", "Bad\x00title"]
)
def test_invalid_title_never_contacts_server(generated_title_client, task_title):
    _, connection, thread_identifier, _, original = generated_title_client
    with pytest.raises(ValueError, match="plain task title"):
        title_command.set_generated_session_title(
            thread_identifier, original.name_digest, task_title
        )
    connection.assert_not_called()


@pytest.mark.parametrize(
    "environment",
    [
        {"CODEX_SESSION_SOCKET_PATH": ""},
        {"CLAWDE_AGENT_NAME": "steward"},
        {"OPENCLAW_GATEWAY_PORT": "18789"},
    ],
)
def test_noninteractive_command_does_not_contact_server(
    generated_title_client, monkeypatch, environment
):
    _, connection, thread_identifier, _, original = generated_title_client
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(ValueError, match="private interactive Codex session"):
        title_command.set_generated_session_title(
            thread_identifier, original.name_digest, "Restore useful session titles"
        )
    connection.assert_not_called()


def test_failed_metadata_request_returns_failure_without_blocking_user_work(
    monkeypatch, capsys
):
    monkeypatch.setattr(
        title_command.sys,
        "argv",
        [
            "command",
            "--thread-id",
            "thread",
            "--expected-name-digest",
            "digest",
            "Task",
        ],
    )
    monkeypatch.setattr(
        title_command,
        "set_generated_session_title",
        Mock(side_effect=TimeoutError("metadata timed out")),
    )
    assert title_command.main() == 1
    assert "metadata timed out" in capsys.readouterr().err
