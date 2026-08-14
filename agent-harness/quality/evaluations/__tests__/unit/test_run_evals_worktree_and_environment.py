from run_evals_worktree_and_environment import build_filtered_environment


def test_isolation_strips_the_interactive_reply_shape_marker(monkeypatch):
    monkeypatch.setenv(
        "AGENT_INTERACTIVE_PREFERENCES_PATH", "/some/interactive/preferences.md"
    )
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("PATH", "/usr/bin:/bin")

    filtered = build_filtered_environment()

    assert "AGENT_INTERACTIVE_PREFERENCES_PATH" not in filtered
    assert "CLAUDECODE" not in filtered
    assert filtered["PATH"] == "/usr/bin:/bin"
