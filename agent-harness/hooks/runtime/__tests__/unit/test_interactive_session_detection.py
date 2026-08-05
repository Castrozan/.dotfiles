import interactive_session_detection


def test_opencode_interactive_preferences_mark_the_session_as_keyboard_driven(
    monkeypatch,
):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.delenv("CLAUDE_INTERACTIVE_PREFERENCES_PATH", raising=False)
    monkeypatch.setenv(
        "OPENCODE_INTERACTIVE_PREFERENCES_PATH",
        "/nix/store/opencode-interactive-session-only-instructions.md",
    )

    assert interactive_session_detection.is_keyboard_driven_interactive_session()
