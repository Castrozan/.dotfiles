CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER = "CLAWDE_RESUME_FLAG"


def write_interactive_preferences_file(tmp_path):
    interactive_preferences_file = tmp_path / "interactive-preferences.md"
    interactive_preferences_file.write_text("interactive reply-shape rules")
    return interactive_preferences_file


def set_interactive_preferences_environment(monkeypatch, module, interactive_file):
    monkeypatch.setenv(
        module.INTERACTIVE_PREFERENCES_FILE_PATH_ENVIRONMENT_VARIABLE_NAME,
        str(interactive_file),
    )


def test_appends_interactive_preferences_for_keyboard_session(
    tmp_path, monkeypatch, workspace_launcher_module
):
    interactive_file = write_interactive_preferences_file(tmp_path)
    set_interactive_preferences_environment(
        monkeypatch, workspace_launcher_module, interactive_file
    )
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER, raising=False)

    arguments = workspace_launcher_module.build_interactive_preferences_system_prompt_arguments()

    assert arguments == ["--append-system-prompt", "interactive reply-shape rules"]


def test_scrub_removes_interactive_preferences_for_clawde_background_agent(
    tmp_path, monkeypatch, workspace_launcher_module
):
    interactive_file = write_interactive_preferences_file(tmp_path)
    set_interactive_preferences_environment(
        monkeypatch, workspace_launcher_module, interactive_file
    )
    monkeypatch.setenv(CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER, "--continue")

    workspace_launcher_module.scrub_interactive_preferences_environment_for_clawde_background_agent()

    import os

    assert (
        workspace_launcher_module.INTERACTIVE_PREFERENCES_FILE_PATH_ENVIRONMENT_VARIABLE_NAME
        not in os.environ
    )
    assert (
        workspace_launcher_module.build_interactive_preferences_system_prompt_arguments()
        == []
    )


def test_scrub_removes_interactive_preferences_when_clawde_marker_is_empty(
    tmp_path, monkeypatch, workspace_launcher_module
):
    interactive_file = write_interactive_preferences_file(tmp_path)
    set_interactive_preferences_environment(
        monkeypatch, workspace_launcher_module, interactive_file
    )
    monkeypatch.setenv(CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER, "")

    workspace_launcher_module.scrub_interactive_preferences_environment_for_clawde_background_agent()

    assert (
        workspace_launcher_module.build_interactive_preferences_system_prompt_arguments()
        == []
    )


def test_scrub_keeps_interactive_preferences_for_keyboard_session(
    tmp_path, monkeypatch, workspace_launcher_module
):
    interactive_file = write_interactive_preferences_file(tmp_path)
    set_interactive_preferences_environment(
        monkeypatch, workspace_launcher_module, interactive_file
    )
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER, raising=False)

    workspace_launcher_module.scrub_interactive_preferences_environment_for_clawde_background_agent()

    assert (
        workspace_launcher_module.build_interactive_preferences_system_prompt_arguments()
        == ["--append-system-prompt", "interactive reply-shape rules"]
    )
