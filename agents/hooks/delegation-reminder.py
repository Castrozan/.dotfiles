#!/usr/bin/env python3
"""delegation-reminder.py - Remind about delegation rules and suggest appropriate subagents."""

import json
import re
import sys

# Mapping of patterns to recommended subagents
# Format: (patterns, subagent, description)
DELEGATION_MAPPINGS = [
    # dotfiles-expert: repository-specific operations
    (
        [
            r"rebuild",
            r"home-manager\s+switch",
            r"nixos-rebuild",
            r"home/modules/",
            r"users/\w+/",
            r"flake\.(nix|lock)",
            r"agenix",
            r"secrets/",
        ],
        "dotfiles-expert",
        "Repository structure, module patterns, rebuild workflow, secrets management"
    ),
    # nix-expert: pure Nix language questions
    (
        [
            r"nix\s+(eval|repl|build)",
            r"derivation",
            r"overlay",
            r"mkIf|mkMerge|mkOption",
            r"lazy\s+evaluation",
            r"fixed.?point",
            r"devenv",
            r"flake\s+(input|output)",
        ],
        "nix-expert",
        "Nix language, expressions, derivations, module system internals"
    ),
    # agent-architect: agent/skill/rule design
    (
        [
            r"agents/subagent/",
            r"agents/rules/",
            r"agents/skills/",
            r"SKILL\.md",
            r"create.*agent",
            r"design.*agent",
            r"write.*skill",
            r"agent.*prompt",
        ],
        "agent-architect",
        "Agent design, skill creation, rule writing, prompt engineering"
    ),
    # claude-expert: Claude Code CLI specifics
    (
        [
            r"claude.*config",
            r"claude.*hook",
            r"claude.*mcp",
            r"\.claude/",
            r"settings\.json",
            r"claude.*permission",
            r"claude.*plugin",
        ],
        "claude-expert",
        "Claude Code CLI configuration, hooks, MCP servers, plugins"
    ),
    # ralph-expert: Ralph TUI and PRD workflows
    (
        [
            r"ralph",
            r"PRD",
            r"product.*requirement",
            r"tracker",
            r"ralph.*loop",
        ],
        "ralph-expert",
        "Ralph TUI, PRD creation, task tracking, AI-driven workflows"
    ),
]


def check_command_delegation(command: str) -> tuple[str, str] | None:
    """Check if a command matches any delegation pattern."""
    command_lower = command.lower()

    for patterns, subagent, description in DELEGATION_MAPPINGS:
        for pattern in patterns:
            if re.search(pattern, command_lower, re.IGNORECASE):
                return subagent, description

    return None


def check_prompt_delegation(prompt: str) -> tuple[str, str] | None:
    """Check if user prompt mentions topics that warrant delegation."""
    prompt_lower = prompt.lower()

    # Additional prompt-specific patterns
    prompt_patterns = [
        # dotfiles-expert
        (
            [r"dotfiles?", r"add.*module", r"create.*module"],
            "dotfiles-expert",
            "Repository structure, module patterns, rebuild workflow"
        ),
        # nix-expert
        (
            [r"nix\s+expression", r"nix\s+syntax", r"how.*nix.*work"],
            "nix-expert",
            "Nix language, expressions, evaluation"
        ),
    ]

    all_patterns = DELEGATION_MAPPINGS + prompt_patterns

    for patterns, subagent, description in all_patterns:
        for pattern in patterns:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                return subagent, description

    return None


def format_delegation_reminder(subagent: str, description: str, context: str) -> str:
    """Format the delegation reminder message."""
    return (
        f"DELEGATION REMINDER: Stop everything and use @{subagent}\n"
        f"Expertise: {description}\n\n"
        f"\"The agent is the only one approved to do this job.\"\n\n"
        f"Send the raw context and user prompt to the agent.\"\n\n"
        f"Context: {context}"
    )


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Handle Bash commands
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if not command:
            sys.exit(0)

        result = check_command_delegation(command)
        if result:
            subagent, description = result
            message = format_delegation_reminder(
                subagent, description, f"Command: {command[:100]}"
            )
            output = {"continue": True, "systemMessage": message}
            print(json.dumps(output))
        sys.exit(0)

    # Handle user prompts (for UserPromptSubmit hook)
    prompt = data.get("prompt", "")
    if prompt:
        result = check_prompt_delegation(prompt)
        if result:
            subagent, description = result
            message = format_delegation_reminder(
                subagent, description, f"Prompt mentions: {subagent}-related topics"
            )
            output = {"continue": True, "systemMessage": message}
            print(json.dumps(output))
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
