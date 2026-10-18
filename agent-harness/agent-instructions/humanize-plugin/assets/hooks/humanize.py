import json
import re
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "hooks/rules"))
sys.path.insert(0, str(PLUGIN_ROOT / "hooks/vendor"))


def session_instructions():
    from reply_format_instructions import expand_reply_format_instructions

    policy = PLUGIN_ROOT / "skills/humanize/references/interactive-communication.md"
    text = expand_reply_format_instructions(policy.read_text(encoding="utf-8"))
    return re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: f"{match[1]} ({(policy.parent / match[2].split('#')[0]).resolve()})",
        text,
    )


def stop_decision(payload):
    if payload.get("stop_hook_active"):
        return {}
    reply = payload.get("reply_text") or payload.get("last_assistant_message")
    if not reply:
        from transcript import final_turn_request_and_reply

        _, reply = final_turn_request_and_reply(payload)
    if not reply:
        return {}
    from reply_rule_catalog import template_violations_in_reply
    from reply_rule_feedback import bounce_guidance

    violations = template_violations_in_reply(reply)
    if not violations:
        return {}
    return {"decision": "block", "reason": bounce_guidance(violations)}


def hook_output(payload):
    event = payload.get("hook_event_name")
    if event == "SessionStart":
        return {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": session_instructions(),
            }
        }
    if event == "Stop":
        return stop_decision(payload)
    return {}


def main():
    payload = {}
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("Hook input must be a JSON object")
        output = hook_output(payload)
    except Exception as error:
        reason = f"Humanize validation could not run: {type(error).__name__}: {error}. Repair the plugin before retrying."
        if (
            isinstance(payload, dict)
            and payload.get("hook_event_name") == "SessionStart"
        ):
            output = {"continue": False, "stopReason": reason}
        else:
            output = {"decision": "block", "reason": reason}
    print(json.dumps(output))


if __name__ == "__main__":
    main()
