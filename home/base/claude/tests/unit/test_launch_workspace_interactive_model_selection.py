CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER = "CLAWDE_RESUME_FLAG"
INTERACTIVE_MODEL = "claude-fable-5[1m]"


def set_interactive_model_environment(monkeypatch, module):
    monkeypatch.setenv(
        module.INTERACTIVE_MODEL_ENVIRONMENT_VARIABLE_NAME, INTERACTIVE_MODEL
    )


def test_injects_model_selection_for_keyboard_session(
    monkeypatch, workspace_launcher_module
):
    set_interactive_model_environment(monkeypatch, workspace_launcher_module)
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER, raising=False)

    arguments = workspace_launcher_module.build_interactive_model_selection_arguments()

    assert arguments == ["--model", INTERACTIVE_MODEL]


def test_no_model_selection_when_environment_unset(
    monkeypatch, workspace_launcher_module
):
    monkeypatch.delenv(
        workspace_launcher_module.INTERACTIVE_MODEL_ENVIRONMENT_VARIABLE_NAME,
        raising=False,
    )

    assert workspace_launcher_module.build_interactive_model_selection_arguments() == []


def test_no_model_selection_when_environment_is_empty(
    monkeypatch, workspace_launcher_module
):
    monkeypatch.setenv(
        workspace_launcher_module.INTERACTIVE_MODEL_ENVIRONMENT_VARIABLE_NAME, ""
    )

    assert workspace_launcher_module.build_interactive_model_selection_arguments() == []


def test_scrub_removes_model_selection_for_clawde_background_agent(
    monkeypatch, workspace_launcher_module
):
    set_interactive_model_environment(monkeypatch, workspace_launcher_module)
    monkeypatch.setenv(CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER, "--continue")

    workspace_launcher_module.scrub_interactive_only_environment_for_clawde_background_agent()

    assert workspace_launcher_module.build_interactive_model_selection_arguments() == []


def test_scrub_keeps_model_selection_for_keyboard_session(
    monkeypatch, workspace_launcher_module
):
    set_interactive_model_environment(monkeypatch, workspace_launcher_module)
    monkeypatch.delenv(CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER, raising=False)

    workspace_launcher_module.scrub_interactive_only_environment_for_clawde_background_agent()

    assert workspace_launcher_module.build_interactive_model_selection_arguments() == [
        "--model",
        INTERACTIVE_MODEL,
    ]
