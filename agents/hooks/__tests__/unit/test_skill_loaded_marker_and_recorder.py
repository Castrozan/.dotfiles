from pathlib import Path

import record_skill_invocation_handler
import skill_loaded_marker


def test_marker_path_templates_skill_name_and_sanitizes_session_id(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", str(tmp_path))

    marker_path = skill_loaded_marker.skill_loaded_marker_path(
        "docs", "session/with:weird chars"
    )

    assert marker_path == tmp_path / "docs-skill-loaded-session-with-weird-chars.marker"


def test_marker_path_defaults_to_the_tmp_directory(monkeypatch):
    monkeypatch.delenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", raising=False)

    marker_path = skill_loaded_marker.skill_loaded_marker_path("instructions", "abc")

    assert marker_path == Path("/tmp/instructions-skill-loaded-abc.marker")


def test_recorded_marker_is_detected_by_has_skill_loaded(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", str(tmp_path))

    assert not skill_loaded_marker.has_skill_loaded("docs", "session-a")
    skill_loaded_marker.record_skill_loaded("docs", "session-a")
    assert skill_loaded_marker.has_skill_loaded("docs", "session-a")
    assert not skill_loaded_marker.has_skill_loaded("docs", "session-b")
    assert not skill_loaded_marker.has_skill_loaded("instructions", "session-a")


def test_canonical_skill_name_strips_the_namespace_prefix():
    assert record_skill_invocation_handler.canonical_skill_name("plugin:docs") == "docs"
    assert (
        record_skill_invocation_handler.canonical_skill_name("marketplace:nix") == "nix"
    )
    assert record_skill_invocation_handler.canonical_skill_name("instructions") == (
        "instructions"
    )


def test_handle_records_nothing_without_a_skill_name(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", str(tmp_path))

    assert record_skill_invocation_handler.handle({"tool_input": {}}) is None
    assert record_skill_invocation_handler.handle({"tool_input": {"skill": ""}}) is None
    assert record_skill_invocation_handler.handle({}) is None

    assert list(tmp_path.iterdir()) == []
