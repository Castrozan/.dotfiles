---
name: claude-code-agents
description: Claude Code custom agent YAML format requirements
alwaysApply: false
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<symlink>
Agent files in agents/subagent/ symlinked to ~/.claude/agents/ via home-manager module at home/modules/claude/agents.nix.
</symlink>

<format>
YAML frontmatter description field MUST be single-line quoted string with \n escape sequences for newlines. Multi-line YAML strings break Claude Code agent discovery. Required fields: name, description, model, color.
</format>

<example>
---
name: agent-name
description: "First paragraph.\n\nExamples:\n\n<example>\nuser: \"question\"\nassistant: \"response\"\n</example>"
model: opus
color: magenta
---
</example>

<rules>
Always use model: opus for custom agents. After modifying agent files: run rebuild, then restart Claude Code.
</rules>
