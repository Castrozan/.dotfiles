def require(condition, message):
    if not condition:
        raise ValueError(message)


def resume_arguments(plan):
    return [
        "--sandbox",
        "danger-full-access",
        "--ask-for-approval",
        "never",
        "--profile",
        "dotfiles-interactive",
        "resume",
        plan["thread_identifier"],
    ]
