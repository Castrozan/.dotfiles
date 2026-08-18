import json

import pytest

import servant_catalog
import servant_identity_handler
import summon_servant

INTERACTIVE_ENV_VAR = "AGENT_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENV_MARKER = "CLAWDE_AGENT_NAME"
STATE_DIR_OVERRIDE_VAR = "SERVANT_IDENTITY_STATE_DIRECTORY"


@pytest.fixture(autouse=True)
def reset_interactive_environment(monkeypatch):
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENV_MARKER, raising=False)
    monkeypatch.delenv(INTERACTIVE_ENV_VAR, raising=False)
    for launch_variable in ("SERVANT_NAME", "SERVANT_CLASS", "SERVANT_MANNER"):
        monkeypatch.delenv(launch_variable, raising=False)


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
    def test_handler_records_the_identity_and_injects_nothing(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv(INTERACTIVE_ENV_VAR, "/nix/store/prefs.md")
        monkeypatch.setenv(STATE_DIR_OVERRIDE_VAR, str(tmp_path))

        result = servant_identity_handler.handle(
            {"hook_event_name": "SessionStart", "session_id": "session-1"}
        )
        assert result is None
        assert json.loads((tmp_path / "servant-identity-session-1.json").read_text())[
            "name"
        ]

    def test_handler_records_the_servant_the_launch_wrapper_summoned(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv(INTERACTIVE_ENV_VAR, "/nix/store/prefs.md")
        monkeypatch.setenv(STATE_DIR_OVERRIDE_VAR, str(tmp_path))
        monkeypatch.setenv("SERVANT_NAME", "Iskandar")
        monkeypatch.setenv("SERVANT_CLASS", "Rider")
        monkeypatch.setenv("SERVANT_MANNER", "King of Conquerors.")

        servant_identity_handler.handle(
            {"hook_event_name": "SessionStart", "session_id": "session-5"}
        )
        recorded = json.loads(
            (tmp_path / "servant-identity-session-5.json").read_text()
        )
        assert recorded["name"] == "Iskandar"
        assert recorded["class"] == "Rider"

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

        servant_identity_handler.handle(
            {"hook_event_name": "SessionStart", "session_id": "session-4"}
        )
        recorded = json.loads(
            (tmp_path / "servant-identity-session-4.json").read_text()
        )
        assert recorded["name"] == servant_catalog.SERVANT_CATALOG[0]["name"]


class TestServantSummoner:
    def test_the_prompt_line_names_the_servant_and_bounds_the_flavour(self):
        line = summon_servant.servant_system_prompt_line(
            {"name": "Iskandar", "manner": "King of Conquerors, boisterous."}
        )
        assert line.startswith("<servant>")
        assert line.endswith("</servant>")
        assert "You are Iskandar." in line
        assert "King of Conquerors, boisterous." in line
        assert "never changes your technical accuracy" in line

    def test_composed_file_keeps_the_base_prompt_and_appends_the_servant(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("TMPDIR", str(tmp_path))
        base_prompt_path = tmp_path / "base.md"
        base_prompt_path.write_text("<interactive>base rules</interactive>\n")

        composed_path = summon_servant.compose_system_prompt_file(
            base_prompt_path, {"name": "Medea", "manner": "Witch of Betrayal."}
        )
        composed_text = composed_path.read_text()
        assert composed_path.parent == tmp_path
        assert "<interactive>base rules</interactive>" in composed_text
        assert "You are Medea." in composed_text

    def test_shell_exports_quote_a_servant_name_with_spaces(self, tmp_path):
        exports = summon_servant.shell_export_lines(
            {"name": "Nero Claudius", "class": "Saber", "manner": "Umu."},
            tmp_path / "composed.md",
        )
        assert "SERVANT_NAME='Nero Claudius'" in exports
        assert any(line.startswith("SERVANT_SYSTEM_PROMPT_FILE=") for line in exports)
