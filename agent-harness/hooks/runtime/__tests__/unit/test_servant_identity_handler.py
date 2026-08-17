import json

import pytest

import servant_catalog
import servant_identity_handler

INTERACTIVE_ENV_VAR = "AGENT_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENV_MARKER = "CLAWDE_AGENT_NAME"
STATE_DIR_OVERRIDE_VAR = "SERVANT_IDENTITY_STATE_DIRECTORY"


@pytest.fixture(autouse=True)
def reset_interactive_environment(monkeypatch):
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENV_MARKER, raising=False)
    monkeypatch.delenv(INTERACTIVE_ENV_VAR, raising=False)


class TestServantCatalog:
    def test_every_entry_carries_name_class_catchphrase_and_manner(self):
        for entry in servant_catalog.SERVANT_CATALOG:
            assert entry["name"].strip()
            assert entry["class"].strip()
            assert entry["catchphrase"].strip()
            assert entry["manner"].strip()

    def test_name_class_keys_are_unique(self):
        keys = [
            (entry["name"], entry["class"]) for entry in servant_catalog.SERVANT_CATALOG
        ]
        assert len(keys) == len(set(keys))

    def test_catalog_has_more_than_one_candidate(self):
        assert len(servant_catalog.SERVANT_CATALOG) > 10

    def test_selection_is_deterministic_per_session_id(self):
        for session_id in ("a", "b", "same-session"):
            first = servant_catalog.select_servant_for_session(session_id)
            second = servant_catalog.select_servant_for_session(session_id)
            assert first == second

    def test_different_session_ids_do_not_all_land_on_one_servant(self):
        selections = {
            (
                servant_catalog.select_servant_for_session(f"session-{n}")["name"],
                servant_catalog.select_servant_for_session(f"session-{n}")["class"],
            )
            for n in range(50)
        }
        assert len(selections) > 1


class TestServantIdentityState:
    def test_state_path_sanitizes_session_id(self, tmp_path, monkeypatch):
        monkeypatch.setenv(STATE_DIR_OVERRIDE_VAR, str(tmp_path))
        path = servant_catalog.servant_identity_state_path("abc/def ghi")
        assert path == tmp_path / "servant-identity-abc-def-ghi.json"

    def test_write_then_read_round_trips(self, tmp_path, monkeypatch):
        monkeypatch.setenv(STATE_DIR_OVERRIDE_VAR, str(tmp_path))
        servant = servant_catalog.SERVANT_CATALOG[0]
        servant_catalog.write_servant_identity("session-x", servant)
        assert servant_catalog.read_servant_identity("session-x") == servant

    def test_read_missing_state_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setenv(STATE_DIR_OVERRIDE_VAR, str(tmp_path))
        assert servant_catalog.read_servant_identity("missing") is None

    def test_write_handles_unwritable_directory(self, tmp_path, monkeypatch):
        monkeypatch.setenv(STATE_DIR_OVERRIDE_VAR, "/dev/null/not-a-directory")
        servant_catalog.write_servant_identity(
            "session-y", servant_catalog.SERVANT_CATALOG[0]
        )


class TestServantIdentityHandler:
    def test_handler_injects_context_for_interactive_session(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv(INTERACTIVE_ENV_VAR, "/nix/store/prefs.md")
        monkeypatch.setenv(STATE_DIR_OVERRIDE_VAR, str(tmp_path))

        result = servant_identity_handler.handle(
            {"hook_event_name": "SessionStart", "session_id": "session-1"}
        )
        assert result is not None
        assert result.additional_context.startswith("SERVANT:")
        assert "summoned as" in result.additional_context
        assert json.loads((tmp_path / "servant-identity-session-1.json").read_text())[
            "name"
        ]

    def test_handler_is_inactive_without_interactive_preferences(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv(STATE_DIR_OVERRIDE_VAR, str(tmp_path))
        result = servant_identity_handler.handle(
            {"hook_event_name": "SessionStart", "session_id": "session-2"}
        )
        assert result is None
        assert not (tmp_path / "servant-identity-session-2.json").exists()

    def test_handler_is_inactive_for_a_clawde_background_agent(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv(INTERACTIVE_ENV_VAR, "/nix/store/prefs.md")
        monkeypatch.setenv(CLAWDE_BACKGROUND_AGENT_ENV_MARKER, "steward")
        monkeypatch.setenv(STATE_DIR_OVERRIDE_VAR, str(tmp_path))
        result = servant_identity_handler.handle(
            {"hook_event_name": "SessionStart", "session_id": "session-3"}
        )
        assert result is None
        assert not (tmp_path / "servant-identity-session-3.json").exists()

    def test_handler_never_re_rolls_an_existing_identity(self, tmp_path, monkeypatch):
        monkeypatch.setenv(INTERACTIVE_ENV_VAR, "/nix/store/prefs.md")
        monkeypatch.setenv(STATE_DIR_OVERRIDE_VAR, str(tmp_path))
        servant_catalog.write_servant_identity(
            "session-4", servant_catalog.SERVANT_CATALOG[0]
        )

        result = servant_identity_handler.handle(
            {"hook_event_name": "SessionStart", "session_id": "session-4"}
        )
        assert result is not None
        assert servant_catalog.SERVANT_CATALOG[0]["name"] in result.additional_context

    def test_formatter_lists_name_class_catchphrase_and_manner(self):
        servant = {
            "name": "Nero Claudius",
            "class": "Saber",
            "catchphrase": "Umu",
            "manner": "Radiant, theatrical, imperial.",
        }
        text = servant_identity_handler.format_servant_context(servant)
        assert "Nero Claudius (Saber)" in text
        assert "Umu" in text
        assert "Radiant" in text
