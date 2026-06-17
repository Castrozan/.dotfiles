import os

INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER = "CLAWDE_RESUME_FLAG"


def is_clawde_background_agent_session() -> bool:
    return CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER in os.environ


def is_keyboard_driven_interactive_session() -> bool:
    if is_clawde_background_agent_session():
        return False
    return bool(os.environ.get(INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE))
