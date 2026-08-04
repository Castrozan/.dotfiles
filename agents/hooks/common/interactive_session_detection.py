import os

INTERACTIVE_SESSION_ENVIRONMENT_VARIABLES = (
    "CLAUDE_INTERACTIVE_PREFERENCES_PATH",
    "OPENCODE_INTERACTIVE_PREFERENCES_PATH",
)
CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER = "CLAWDE_AGENT_NAME"


def is_clawde_background_agent_session() -> bool:
    return CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER in os.environ


def is_keyboard_driven_interactive_session() -> bool:
    if is_clawde_background_agent_session():
        return False
    return any(
        os.environ.get(environment_variable)
        for environment_variable in INTERACTIVE_SESSION_ENVIRONMENT_VARIABLES
    )
