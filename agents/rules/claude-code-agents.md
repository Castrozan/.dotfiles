---
description: Claude Code custom agent YAML format requirements
alwaysApply: false
---

Do not change this file if not requested or if the change does not follow the pattern that focuses on token usage and information density. Follow these rules when creating or editing Claude Code agents.

Agent files in agents/subagent/ are symlinked to ~/.claude/agents/ via home-manager module at home/modules/claude/agents.nix. YAML frontmatter `description` field MUST be single-line quoted string with `\n` escape sequences for newlines. Multi-line YAML strings break Claude Code agent discovery. Required fields: name, description, model, color. Example format:

```yaml
---
name: agent-name
description: "First paragraph.\n\nExamples:\n\n<example>\nuser: \"question\"\nassistant: \"response\"\n</example>"
model: sonnet
color: magenta
---
```
