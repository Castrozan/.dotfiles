#!/usr/bin/env python3
"""subagent-context-reminder.py - Remind to provide full context when using subagents."""

import json
import sys

# Subagent types that particularly benefit from context
CONTEXT_CRITICAL_SUBAGENTS = [
    "general-purpose",
    "Explore",
    "Plan",
    "agent-architect",
    "nix-expert",
    "dotfiles-expert",
    "claude-expert",
    "claude-code-guide",
]

def get_context_tips(subagent_type: str) -> list[str]:
    """Get specific context tips for different subagent types."""
    tips = [
        "Include relevant file paths and line numbers",
        "Mention current working directory if relevant",
        "Describe what you've already tried or discovered",
        "Include error messages or unexpected behavior",
    ]

    if subagent_type in ["general-purpose", "Explore"]:
        tips.append("Specify the scope of exploration (specific files, patterns, or broad codebase)")

    elif subagent_type == "Plan":
        tips.append("Describe requirements, constraints, and desired outcomes clearly")

    elif subagent_type in ["agent-architect"]:
        tips.append("Describe the agent's purpose, tools needed, and workflow patterns")

    elif subagent_type in ["nix-expert", "dotfiles-expert"]:
        tips.append("Mention your NixOS version, current config structure, and what's not working")

    elif subagent_type in ["claude-expert", "claude-code-guide"]:
        tips.append("Include your Claude Code version and specific feature questions")

    return tips

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name != "Task":
        sys.exit(0)

    subagent_type = tool_input.get("subagent_type", "")
    prompt = tool_input.get("prompt", "")

    # Only provide reminder for context-critical subagents
    if not subagent_type or subagent_type not in CONTEXT_CRITICAL_SUBAGENTS:
        sys.exit(0)

    # Check if prompt is very short (likely missing context)
    prompt_length = len(prompt.strip())
    is_short_prompt = prompt_length < 100

    # Check for common context indicators
    has_file_reference = "file:" in prompt.lower() or ".py" in prompt or ".nix" in prompt
    has_error_info = "error" in prompt.lower() or "fail" in prompt.lower()
    has_location_info = "directory" in prompt.lower() or "cwd" in prompt.lower()

    context_score = sum([
        has_file_reference,
        has_error_info,
        has_location_info,
        not is_short_prompt
    ])

    # Only warn if context seems insufficient
    if context_score >= 2:
        sys.exit(0)

    tips = get_context_tips(subagent_type)
    tip_text = "\n".join([f"  • {tip}" for tip in tips[:4]])

    message = (
        f"🤖 SUBAGENT CONTEXT REMINDER: @{subagent_type} loses context between calls\n\n"
        "Consider including:\n"
        f"{tip_text}\n\n"
        "💡 Subagents work best with complete context in each delegation."
    )

    output = {
        "continue": True,
        "systemMessage": message
    }
    print(json.dumps(output))

    sys.exit(0)

if __name__ == "__main__":
    main()