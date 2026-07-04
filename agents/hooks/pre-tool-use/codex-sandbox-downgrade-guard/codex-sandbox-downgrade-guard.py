from __future__ import annotations

import json
import sys

CODEX_LAUNCH_TOOL_NAME = "mcp__codex__codex"
REQUIRED_SANDBOX_MODE = "danger-full-access"
REQUIRED_APPROVAL_POLICY = "never"


def describe_sandbox_downgrade(requested_sandbox_mode, source_label):
    if requested_sandbox_mode is None:
        return None
    if requested_sandbox_mode == REQUIRED_SANDBOX_MODE:
        return None
    return (
        f"{source_label} requests sandbox {requested_sandbox_mode!r}, "
        f"weaker than the mandatory {REQUIRED_SANDBOX_MODE!r}"
    )


def describe_approval_downgrade(requested_approval_policy, source_label):
    if requested_approval_policy is None:
        return None
    if requested_approval_policy == REQUIRED_APPROVAL_POLICY:
        return None
    return (
        f"{source_label} requests approval policy {requested_approval_policy!r}, "
        f"which reintroduces the approval prompts the session must never have "
        f"(required {REQUIRED_APPROVAL_POLICY!r})"
    )


def find_first_downgrade(tool_input):
    raw_config_overrides = tool_input.get("config")
    inline_config_overrides = (
        raw_config_overrides if isinstance(raw_config_overrides, dict) else {}
    )
    ordered_downgrade_checks = [
        describe_sandbox_downgrade(tool_input.get("sandbox"), "sandbox parameter"),
        describe_approval_downgrade(
            tool_input.get("approval-policy"), "approval-policy parameter"
        ),
        describe_sandbox_downgrade(
            inline_config_overrides.get("sandbox_mode"),
            "config.sandbox_mode override",
        ),
        describe_approval_downgrade(
            inline_config_overrides.get("approval_policy"),
            "config.approval_policy override",
        ),
    ]
    for downgrade_description in ordered_downgrade_checks:
        if downgrade_description is not None:
            return downgrade_description
    return None


def emit_denial_and_exit(downgrade_description):
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Codex sessions must launch at full bypass and this call {downgrade_description}. "
                f"Re-invoke {CODEX_LAUNCH_TOOL_NAME} without the sandbox, approval-policy, or any "
                f"config sandbox/approval override so it inherits danger-full-access and never from "
                f"~/.codex/config.toml."
            ),
        }
    }
    print(json.dumps(output))
    sys.exit(0)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if data.get("tool_name", "") != CODEX_LAUNCH_TOOL_NAME:
        sys.exit(0)

    tool_input = data.get("tool_input", {}) or {}
    downgrade_description = find_first_downgrade(tool_input)
    if downgrade_description is None:
        sys.exit(0)

    emit_denial_and_exit(downgrade_description)


if __name__ == "__main__":
    main()
