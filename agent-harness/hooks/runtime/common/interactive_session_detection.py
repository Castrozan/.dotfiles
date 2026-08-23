import os

INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE = "AGENT_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER = "CLAWDE_AGENT_NAME"
CLAWDE_AGENT_WORKSPACES_ENVIRONMENT_VARIABLE = "CLAWDE_AGENTS_DIRECTORY"
DEFAULT_CLAWDE_AGENT_WORKSPACES_DIRECTORY = "~/clawde"


def clawde_agent_workspaces_directory() -> str:
    configured = os.environ.get(CLAWDE_AGENT_WORKSPACES_ENVIRONMENT_VARIABLE)
    return os.path.realpath(
        os.path.expanduser(configured or DEFAULT_CLAWDE_AGENT_WORKSPACES_DIRECTORY)
    )


def is_session_running_inside_a_clawde_agent_workspace() -> bool:
    workspaces_directory = clawde_agent_workspaces_directory()
    return os.path.realpath(os.getcwd()).startswith(workspaces_directory + os.sep)


def is_clawde_background_agent_session() -> bool:
    if CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER in os.environ:
        return True
    return is_session_running_inside_a_clawde_agent_workspace()


def is_keyboard_driven_interactive_session() -> bool:
    if is_clawde_background_agent_session():
        return False
    return bool(os.environ.get(INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE))
