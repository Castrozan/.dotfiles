import pytest
import record_skill_invocation_handler
import skill_loaded_marker
from hook_state_directory import hook_state_directory


def test_marker_path_templates_skill_name_and_sanitizes_session_id(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", str(tmp_path))

    marker_path = skill_loaded_marker.skill_loaded_marker_path(
        "docs", "session/with:weird chars"
    )

    assert marker_path == str(
        tmp_path / "docs-skill-loaded-session-with-weird-chars.marker"
    )


def test_marker_path_defaults_to_a_private_state_directory(tmp_path, monkeypatch):
    monkeypatch.delenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))

    marker_path = skill_loaded_marker.skill_loaded_marker_path("instructions", "abc")

    assert marker_path == str(
        tmp_path / "agent-hooks/instructions-skill-loaded-abc.marker"
    )
    assert (tmp_path / "agent-hooks").stat().st_mode & 0o777 == 0o700


def test_hook_state_directory_refuses_a_symlink(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    target_directory = tmp_path / "unrelated"
    target_directory.mkdir(mode=0o755)
    (tmp_path / "agent-hooks").symlink_to(target_directory, target_is_directory=True)

    with pytest.raises(PermissionError):
        hook_state_directory()

    assert target_directory.stat().st_mode & 0o777 == 0o755


def test_recorded_marker_is_detected_by_has_skill_loaded(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", str(tmp_path))

    assert not skill_loaded_marker.has_skill_loaded("docs", "session-a")
    skill_loaded_marker.record_skill_loaded("docs", "session-a")
    assert skill_loaded_marker.has_skill_loaded("docs", "session-a")
    assert not skill_loaded_marker.has_skill_loaded("docs", "session-b")
    assert not skill_loaded_marker.has_skill_loaded("instructions", "session-a")


def test_clear_removes_only_the_selected_skill_marker(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_SKILL_LOADED_MARKER_STATE_DIRECTORY", str(tmp_path))
    skill_loaded_marker.record_skill_loaded("humanize", "session-a")
    skill_loaded_marker.record_skill_loaded("docs", "session-a")

    skill_loaded_marker.clear_skill_loaded("humanize", "session-a")

    assert not skill_loaded_marker.has_skill_loaded("humanize", "session-a")
    assert skill_loaded_marker.has_skill_loaded("docs", "session-a")


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
