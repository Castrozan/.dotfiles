from __future__ import annotations

import sys
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in [_MODULE_DIRECTORY] + [
    ancestor / "common" for ancestor in _MODULE_DIRECTORY.parents
]:
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

from hook_dispatch import HandlerResult  # noqa: E402

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


def build_denial_reason(downgrade_description):
    return (
        f"Codex sessions must launch at full bypass and this call {downgrade_description}. "
        f"Re-invoke {CODEX_LAUNCH_TOOL_NAME} without the sandbox, approval-policy, or any "
        f"config sandbox/approval override so it inherits danger-full-access and never from "
        f"~/.codex/config.toml."
    )


def handle(hook_input):
    if hook_input.get("tool_name", "") != CODEX_LAUNCH_TOOL_NAME:
        return None
    tool_input = hook_input.get("tool_input", {}) or {}
    downgrade_description = find_first_downgrade(tool_input)
    if downgrade_description is None:
        return None
    return HandlerResult(
        decision="deny", reason=build_denial_reason(downgrade_description)
    )
