---
name: claude-code-agents
description: Claude Code custom agent YAML format requirements
alwaysApply: false
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<format>
Skills live in agents/skills/name/SKILL.md, deployed to ~/.claude/skills/ via home-manager module at home/modules/claude/skills.nix. YAML frontmatter requires name and description fields.
</format>

<example>
---
name: skill-name
description: When to use this skill and what it does.
---

Body with XML-tagged instructions in dense prose format.
</example>

<rules>
After modifying skill files: run rebuild, then restart Claude Code.
</rules>
