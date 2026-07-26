import json
import subprocess
import sys

from run_evals_worktree_and_environment import REPO_ROOT

HOOK_SCRIPT_SEARCH_ROOT = REPO_ROOT / "agents" / "hooks"


def find_hook_script(hook_filename):
    matches = sorted(HOOK_SCRIPT_SEARCH_ROOT.rglob(hook_filename))
    return matches[0] if matches else None


def synthesize_hook_event(trigger):
    tool_input = {key: value for key, value in trigger.items() if key != "tool"}
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": trigger.get("tool", ""),
        "tool_input": tool_input,
        "cwd": str(REPO_ROOT),
    }


def hook_blocked(returncode, stdout_json):
    if returncode == 2:
        return True
    if not isinstance(stdout_json, dict):
        return False
    if stdout_json.get("continue") is False:
        return True
    if stdout_json.get("decision") == "block":
        return True
    hook_specific_output = stdout_json.get("hookSpecificOutput")
    if (
        isinstance(hook_specific_output, dict)
        and hook_specific_output.get("permissionDecision") == "deny"
    ):
        return True
    return False


def hook_message(stdout, stderr, stdout_json):
    message_parts = [stderr]
    if isinstance(stdout_json, dict):
        message_parts.append(stdout_json.get("systemMessage") or "")
        message_parts.append(stdout_json.get("reason") or "")
        hook_specific_output = stdout_json.get("hookSpecificOutput")
        if isinstance(hook_specific_output, dict):
            message_parts.append(hook_specific_output.get("additionalContext") or "")
            message_parts.append(
                hook_specific_output.get("permissionDecisionReason") or ""
            )
    else:
        message_parts.append(stdout)
    return "\n".join(part for part in message_parts if part)


def interpret_hook_result(returncode, stdout, stderr, assertions):
    try:
        stdout_json = json.loads(stdout) if stdout.strip() else None
    except json.JSONDecodeError:
        stdout_json = None

    blocked = hook_blocked(returncode, stdout_json)
    message = hook_message(stdout, stderr, stdout_json)

    failures = []
    if "hook_blocks" in assertions and assertions["hook_blocks"] != blocked:
        failures.append(
            f"expected hook_blocks={assertions['hook_blocks']}, got {blocked}"
        )
    expected_substring = assertions.get("message_contains")
    if expected_substring and expected_substring not in message:
        failures.append(f"hook message did not contain {expected_substring!r}")
    return failures


def evaluate_hook_test(test):
    hook_filename = test.get("hook")
    script_path = find_hook_script(hook_filename)
    if script_path is None:
        return [f"hook script not found: {hook_filename}"]

    completed = subprocess.run(
        [sys.executable, str(script_path)],
        input=json.dumps(synthesize_hook_event(test.get("trigger", {}))),
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return interpret_hook_result(
        completed.returncode,
        completed.stdout,
        completed.stderr,
        test.get("assertions", {}),
    )
