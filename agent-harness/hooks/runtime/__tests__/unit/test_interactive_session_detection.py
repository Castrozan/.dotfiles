import interactive_session_detection


def test_shared_interactive_preferences_mark_the_session_as_keyboard_driven(
    monkeypatch,
):
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.setenv(
        "AGENT_INTERACTIVE_PREFERENCES_PATH",
        "/nix/store/interactive-session-only-instructions.md",
    )

    assert interactive_session_detection.is_keyboard_driven_interactive_session()
