from __future__ import annotations

from hook_dispatch import HandlerResult


def handle(hook_input):
    instructions = hook_input.get("_codex_client_developer_instructions")
    if instructions:
        return HandlerResult(additional_context=instructions)
    return None
