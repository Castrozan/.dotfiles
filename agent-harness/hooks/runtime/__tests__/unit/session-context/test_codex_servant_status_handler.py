import pytest

import codex_servant_status_handler as status_handler
from codex_app_server_client import CodexThreadTitle
import servant_identity_handler
from hook_dispatch import CODEX_SURFACE, HookHandler, run_handlers


def test_footer_name_matches_injected_servant_for_minted_thread(
    session_client, tmp_path
):
    client, connection = session_client
    payload = {"session_id": "codex-name-probe", "source": "startup"}
    identity = servant_identity_handler.servant_for_hook_input(payload)
    assert status_handler.handle(payload) is None
    connection.assert_called_once_with(str(tmp_path / "private.sock"))
    client.thread_title.assert_called_once_with("codex-name-probe")
    client.set_thread_name.assert_called_once_with("codex-name-probe", identity["name"])


@pytest.mark.parametrize("source", ["resume", "compact"])
def test_repeated_session_does_not_rename_again(session_client, source):
    client, _ = session_client
    payload = {"thread_id": "same-session", "source": source}
    servant = servant_identity_handler.servant_for_hook_input(payload)
    client.thread_title.return_value = CodexThreadTitle(
        f"{servant['name']} | Keep this title", "Original first prompt"
    )
    status_handler.handle(payload)
    client.set_thread_name.assert_not_called()


@pytest.mark.parametrize(
    "title,expected",
    [
        (None, "BB"),
        ("", "BB"),
        ("BB", "BB"),
        ("Bedivere", "BB"),
        ("[BB]", "BB"),
        ("[Bedivere]", "BB"),
        ("Human title", "BB | Human title"),
        ("[Bedivere] Human title", "BB | Human title"),
        ("[BB] Human title", "BB | Human title"),
        ("[BB] | Human title", "BB | Human title"),
        ("Bedivere | Human title", "BB | Human title"),
        ("BB | Human title", "BB | Human title"),
        ("[Mata Hari] Mata Hari | Human title", "BB | Human title"),
        ("[BB] | [Bedivere] Human title", "BB | Human title"),
        ("Lancelot (Berserker) | Human title", "BB | Human title"),
        ("[draft] Human title", "BB | [draft] Human title"),
    ],
)
def test_titles_survive_servant_prefix_replacement(title, expected):
    assert (
        status_handler.servant_thread_name(CodexThreadTitle(title, ""), "BB")
        == expected
    )


@pytest.mark.parametrize("title", [None, "", "BB", "Bedivere", "[BB]", "[Bedivere]"])
def test_servant_only_names_recover_the_native_session_preview(title):
    thread_title = CodexThreadTitle(title, "Fix terminal title")
    assert (
        status_handler.servant_thread_name(thread_title, "BB")
        == "BB | Fix terminal title"
    )


@pytest.mark.parametrize("prompt", ["Fix terminal title", "\nFix  terminal\ttitle\n"])
def test_first_prompt_requests_a_title_before_the_native_preview_exists(
    session_client, prompt
):
    client, _ = session_client
    payload = {
        "session_id": "first-prompt",
        "hook_event_name": "UserPromptSubmit",
        "prompt": prompt,
    }
    servant = servant_identity_handler.servant_for_hook_input(payload)
    client.thread_title.return_value = CodexThreadTitle(servant["name"], "")
    result = status_handler.handle(payload)
    assert "Codex session title command" in result.additional_context
    client.set_thread_name.assert_not_called()


@pytest.mark.parametrize("prompt", [None, 123, [], "", " \n\t"])
def test_empty_or_malformed_first_prompt_keeps_the_plain_servant_name(
    session_client, prompt
):
    client, _ = session_client
    payload = {
        "session_id": "empty-first-prompt",
        "hook_event_name": "UserPromptSubmit",
        "prompt": prompt,
    }
    servant = servant_identity_handler.servant_for_hook_input(payload)
    client.thread_title.return_value = CodexThreadTitle(servant["name"], "")
    status_handler.handle(payload)
    client.set_thread_name.assert_not_called()


def test_followup_prompt_preserves_the_existing_title(session_client):
    client, _ = session_client
    payload = {
        "session_id": "followup-prompt",
        "hook_event_name": "UserPromptSubmit",
        "prompt": "Also fix the footer",
    }
    servant = servant_identity_handler.servant_for_hook_input(payload)
    client.thread_title.return_value = CodexThreadTitle(
        f"{servant['name']} | Fix terminal title", "Original first prompt"
    )
    status_handler.handle(payload)
    client.set_thread_name.assert_not_called()


def test_native_preview_takes_precedence_over_followup_prompt(session_client):
    client, _ = session_client
    payload = {
        "session_id": "recover-prompt",
        "hook_event_name": "UserPromptSubmit",
        "prompt": "Also fix the footer",
    }
    servant = servant_identity_handler.servant_for_hook_input(payload)
    client.thread_title.return_value = CodexThreadTitle(
        f"[{servant['name']}]", "Original first prompt"
    )
    status_handler.handle(payload)
    client.set_thread_name.assert_called_once_with("recover-prompt", servant["name"])


@pytest.mark.parametrize(
    "environment,payload",
    [
        ({"CODEX_SESSION_SOCKET_PATH": ""}, {"session_id": "external"}),
        ({"CLAWDE_AGENT_NAME": "steward"}, {"session_id": "background"}),
        ({"OPENCLAW_GATEWAY_PORT": "18789"}, {"session_id": "gateway"}),
        ({}, {"session_id": "child", "agent_id": "subagent"}),
        ({}, {}),
    ],
)
def test_sessions_outside_private_interactive_thread_do_not_connect(
    session_client, monkeypatch, environment, payload
):
    _, connection = session_client
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    assert status_handler.handle(payload) is None
    connection.assert_not_called()


def test_failed_rename_keeps_persona_context_and_does_not_block_turn(session_client):
    client, _ = session_client
    client.set_thread_name.side_effect = TimeoutError("metadata timed out")
    outcome = run_handlers(
        {"session_id": "failure-probe"},
        [
            HookHandler(handler_module_name="servant_identity_handler"),
            HookHandler(handler_module_name="codex_servant_status_handler"),
        ],
        CODEX_SURFACE,
    )
    assert outcome.additional_context_fragments[0].startswith("Servant: ")
    assert outcome.decision is None
    assert "metadata timed out" in outcome.system_message_fragments[0]
