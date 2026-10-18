import json
import os
import subprocess
import sys

from hook_dispatch import HandlerResult
from interactive_session_detection import is_keyboard_driven_interactive_session


def run_public_hook(hook_input):
    completed = subprocess.run(
        [sys.executable, "-S", os.environ["DOTFILES_WELLPUT_HOOK"]],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    output = json.loads(completed.stdout)
    if not isinstance(output, dict):
        raise ValueError("Wellput hook output must be an object")
    return output


def startup_context_result(output):
    context = output.get("hookSpecificOutput", {}).get("additionalContext", "")
    if not isinstance(context, str):
        raise ValueError("Wellput startup context must be text")
    return HandlerResult(additional_context=context) if context else None


def public_hook_result(output):
    if output.get("decision") == "block" or output.get("continue") is False:
        return HandlerResult(
            decision="block",
            reason=output.get("reason") or output.get("stopReason"),
        )
    return startup_context_result(output)


def handle(hook_input):
    event = hook_input.get("hook_event_name")
    if event not in ("SessionStart", "Stop"):
        return None
    if not is_keyboard_driven_interactive_session():
        return None
    try:
        return public_hook_result(run_public_hook(hook_input))
    except Exception as error:
        return HandlerResult(
            decision="block",
            reason=f"Wellput could not run: {type(error).__name__}: {error}",
        )
