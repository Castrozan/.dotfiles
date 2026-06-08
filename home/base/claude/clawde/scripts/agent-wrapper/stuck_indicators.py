USAGE_LIMIT_MODAL_INDICATORS = [
    "Wait for limit to reset",
    "Adjust monthly spend limit",
    "You've hit your weekly limit",
]

REPL_PROMPT_MARKER = "❯"
AUTOSUGGESTION_GHOST_SEPARATOR = "\xa0"
ONBOARDING_INDICATORS = [
    "Select login method",
    "Choose the text style",
    "Paste code here",
    "Claude account with subscription",
]


def pane_indicates_usage_limit_modal(pane_content: str) -> bool:
    return any(indicator in pane_content for indicator in USAGE_LIMIT_MODAL_INDICATORS)


def pane_is_at_onboarding(pane_content: str) -> bool:
    return any(indicator in pane_content for indicator in ONBOARDING_INDICATORS)


def line_is_idle_repl_prompt(line: str) -> bool:
    stripped = line.strip()
    if stripped == REPL_PROMPT_MARKER or stripped.endswith(" " + REPL_PROMPT_MARKER):
        return True
    return line.startswith(REPL_PROMPT_MARKER + AUTOSUGGESTION_GHOST_SEPARATOR)


def pane_is_at_idle_repl_prompt(pane_content: str) -> bool:
    if pane_is_at_onboarding(pane_content):
        return False
    return any(line_is_idle_repl_prompt(line) for line in pane_content.splitlines())


def pane_poll_is_stuck_evidence(
    current_pane_content: str, previous_pane_content: str | None
) -> bool:
    if pane_is_at_idle_repl_prompt(current_pane_content):
        return False
    if pane_indicates_usage_limit_modal(current_pane_content):
        return True
    return (
        previous_pane_content is not None
        and current_pane_content == previous_pane_content
    )
