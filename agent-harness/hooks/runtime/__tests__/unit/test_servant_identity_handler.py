import pytest
from hook_module_loader import import_hyphenated_hook_module

servant_identity_handler = import_hyphenated_hook_module("servant_identity_handler")

INTERACTIVE_SESSION_ENVIRONMENT = {
    "AGENT_INTERACTIVE_PREFERENCES_PATH": "/nix/store/p.md"
}


@pytest.fixture(autouse=True)
def keyboard_driven_session(monkeypatch):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    for name, value in INTERACTIVE_SESSION_ENVIRONMENT.items():
        monkeypatch.setenv(name, value)


def _handle(session_id, payload_key="session_id"):
    return servant_identity_handler.handle(
        {"hook_event_name": "SessionStart", payload_key: session_id}
    )


class TestNamingTheServant:
    def test_the_line_carries_a_name_and_a_manner(self):
        context = _handle("naming-probe").additional_context
        name, _, personality = context.removeprefix("Servant: ").partition(" - ")
        assert name.strip()
        assert personality.strip()

    def test_the_line_starts_with_the_token_the_rule_looks_for(self):
        assert _handle("token-probe").additional_context.startswith("Servant: ")


class TestResumeKeepsOneServant:
    """Nothing is written down anywhere, so these are the only guarantees a resumed
    conversation has: the harness replays its session id, and the draw is a pure
    function of it."""

    def test_the_same_id_always_draws_the_same_servant(self):
        assert (
            _handle("same-id").additional_context
            == _handle("same-id").additional_context
        )

    def test_a_compact_draws_the_same_servant_as_the_launch(self):
        launched = servant_identity_handler.handle(
            {"hook_event_name": "SessionStart", "session_id": "c9", "source": "startup"}
        )
        compacted = servant_identity_handler.handle(
            {"hook_event_name": "SessionStart", "session_id": "c9", "source": "compact"}
        )
        assert launched.additional_context == compacted.additional_context

    def test_different_ids_do_not_all_collapse_onto_one_servant(self):
        drawn = {_handle(f"spread-{index}").additional_context for index in range(30)}
        assert len(drawn) > 1


class TestSessionsThatGetNoServant:
    def test_a_clawde_agent_keeps_the_identity_it_already_has(self, monkeypatch):
        monkeypatch.setenv("CLAWDE_AGENT_NAME", "steward")
        assert _handle("clawde-probe") is None

    def test_an_agent_workspace_keeps_it_when_the_launcher_marks_nothing(
        self, tmp_path, monkeypatch
    ):
        agent_workspaces_directory = tmp_path / "clawde"
        agent_workspace = agent_workspaces_directory / "monster"
        agent_workspace.mkdir(parents=True)
        monkeypatch.setenv("CLAWDE_AGENTS_DIRECTORY", str(agent_workspaces_directory))
        monkeypatch.chdir(agent_workspace)

        assert _handle("channel-turn-probe") is None

    def test_a_payload_with_no_id_stays_silent(self):
        assert (
            servant_identity_handler.handle({"hook_event_name": "SessionStart"}) is None
        )

    def test_an_empty_id_stays_silent_rather_than_drawing_one_shared_servant(self):
        assert _handle("") is None


class TestOtherHarnessPayloads:
    """Codex registers the same hook config shape as Claude Code but the harnesses
    have not all settled on one key for the conversation, so the handler reads the
    plausible ones rather than going silent on a surface that names it differently."""

    @pytest.mark.parametrize(
        "payload_key", ["session_id", "conversation_id", "thread_id"]
    )
    def test_the_id_is_found_under_each_key_a_surface_may_use(self, payload_key):
        assert _handle("cross-surface", payload_key).additional_context.startswith(
            "Servant: "
        )

    def test_every_key_naming_the_same_conversation_draws_the_same_servant(self):
        by_key = {
            key: _handle("one-conversation", key).additional_context
            for key in ("session_id", "conversation_id", "thread_id")
        }
        assert len(set(by_key.values())) == 1
