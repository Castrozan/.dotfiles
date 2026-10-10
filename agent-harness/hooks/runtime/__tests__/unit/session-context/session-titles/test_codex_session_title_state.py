from codex_session_title_state import (
    generated_session_title_is_current,
    generated_session_title_state_path,
    record_generated_session_title,
)


def test_generated_title_marker_survives_fresh_reads_and_is_thread_scoped(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    record_generated_session_title("first-thread", "generated-name-digest")
    assert generated_session_title_is_current("first-thread", "generated-name-digest")
    assert not generated_session_title_is_current(
        "second-thread", "generated-name-digest"
    )
    assert not generated_session_title_is_current("first-thread", "changed-name-digest")


def test_thread_identifier_cannot_escape_state_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    path = generated_session_title_state_path("../../other-thread")
    assert path.parent == tmp_path / "dotfiles" / "codex-session-titles"
    assert len(path.name) == 64
