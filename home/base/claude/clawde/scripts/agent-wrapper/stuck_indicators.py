USAGE_LIMIT_MODAL_INDICATORS = [
    "Wait for limit to reset",
    "Adjust monthly spend limit",
    "You've hit your weekly limit",
]

AUTHENTICATION_FAILURE_INDICATORS = [
    "Please run /login",
    "API Error: 401",
    "Invalid authentication credentials",
]

STUCK_MODAL_INDICATORS = (
    USAGE_LIMIT_MODAL_INDICATORS + AUTHENTICATION_FAILURE_INDICATORS
)


def pane_indicates_usage_limit_modal(pane_content: str) -> bool:
    return any(indicator in pane_content for indicator in USAGE_LIMIT_MODAL_INDICATORS)


def pane_indicates_authentication_failure(pane_content: str) -> bool:
    return any(
        indicator in pane_content for indicator in AUTHENTICATION_FAILURE_INDICATORS
    )


def pane_indicates_stuck_modal(pane_content: str) -> bool:
    return any(indicator in pane_content for indicator in STUCK_MODAL_INDICATORS)
