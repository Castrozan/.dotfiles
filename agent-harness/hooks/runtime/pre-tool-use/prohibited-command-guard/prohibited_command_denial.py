from hook_dispatch import HandlerResult


def denial_for_violation(tool_name, inspectable_text, violation):
    if violation is None:
        return None
    _pattern, reason = violation
    block_message = (
        f"BLOCKED ({tool_name}): {reason}\nOffending input: {inspectable_text.strip()}"
    )
    return HandlerResult(
        decision="deny", reason=block_message, system_message=block_message
    )
