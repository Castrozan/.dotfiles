---
name: instructions
description: Use when creating skills, agents, system prompts, optimizing AI instructions. Also use when instructions feel stale, vague, or are being ignored by the model. Prompt engineering, context engineering.
---

<extension_decision>
Skill: AI auto-detects relevance, workflow guidance, progressive disclosure.
Script: User explicit control, simple repeatable action, template-based.
</extension_decision>

<skill_format>
Skills live in agents/skills/name/SKILL.md, deployed to IA agents via home-manager. YAML frontmatter requires name and description fields. Short directory names for easy discovery. Body uses XML tags with dense prose. Script-backed skills keep logic in scripts/ subdirectory with SKILL.md as minimal entry point.
</skill_format>

<skill_discovery>
Description drives discovery — models read it semantically to match user intent. Name is just the invocation identifier. Write descriptions as: one-sentence purpose + "Use when..." with natural user phrasings as trigger scenarios. Embed synonyms in prose, not as keyword lists. Add "Do NOT use for..." boundaries when similar skills exist. Keep descriptions under 150 words. All trigger information goes in the description, not the body.
</skill_discovery>

<writing_instructions>
XML tags for structure with descriptive long tag names. Dense prose in imperative voice ("Do X" not "You should do X"). Context over quantity — minimal high-signal tokens. Only add what the model doesn't already know. Challenge each piece: "Does this paragraph justify its token cost?"
</writing_instructions>

<evergreen_instructions>
Instructions become stale when code changes. Write instructions that stay accurate without maintenance.

Pointers over copies: "Run the rebuild script in bin/" not "Run ./bin/rebuild".
Patterns over commands: Document patterns, not exact syntax.
Reference locations: Point to where truth lives, agent reads current state.
No hardcoded paths: Reference things by purpose, not by path.
Intent over implementation: What user wants rarely changes, how to accomplish it evolves.
Version independence: Avoid embedding versions, dates, release names.
</evergreen_instructions>

<unavoidable_specifics>
When exact commands are required: keep in ONE authoritative location, other docs point there. Mark as "verify current command before using".
</unavoidable_specifics>

<self_verification>
When instructions describe HOW: include "Verify current approach by checking [specific file/directory]". Teaches agents to confirm before acting on potentially stale instructions.
</self_verification>

<cohesion>
New instructions are not more important than existing ones. No emphasis markers (CRITICAL, IMPORTANT) for later additions. Instructions should be cohesive — latest additions integrate, not dominate.
</cohesion>

<skill_authoring_preflight>
Before writing any SKILL.md, answer these questions. If any answer is "yes", revise before committing:

- Does the body repeat what the frontmatter description already says? Remove it.
- Does any section belong to a different skill's responsibility? Tool skills document their own API only — workflow composition belongs in workflow skills.
- Are there hardcoded file paths, tokens, or environment-specific values that will go stale? Generalize to patterns or point to where the truth lives.
- Would a dense two-line prose replace a verbose example block without losing clarity? Prefer density.
- Does any content exist only because raw research data was fresh in context? Strip research artifacts — write from synthesized patterns, not from raw dumps.
</skill_authoring_preflight>
