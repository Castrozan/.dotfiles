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
Description drives discovery — models match semantically, so embed synonyms in prose. Every skill description is injected into every agent session; each word is a shared token tax across all interactions. Cap at 2 sentences, ~30 words. Add "Do NOT use for..." only where a sibling skill creates real confusion. All trigger information goes in the description, not the body.
</skill_discovery>

<writing_instructions>
XML tags for structure with descriptive long tag names. Dense prose in imperative voice ("Do X" not "You should do X"). Context over quantity — minimal high-signal tokens. Only add what the model doesn't already know. Challenge each piece: "Does this paragraph justify its token cost?"

Never explain what code does — the model can read it. Document what the model cannot infer: non-obvious constraints, traps where code compiles but behaves wrong, reasons behind surprising design choices, which things must stay in sync and why. If a fact is discoverable by reading the source file, it does not belong in instructions.

A stale instruction is worse than no instruction. When instructions describe code structure that later changes, the model follows the instruction over what it reads, producing confident wrong behavior. Every specific detail is a future liability. Write about forces and constraints, not about current implementation.
</writing_instructions>

<policy_versus_instruction>
Policies and instructions serve different purposes. An instruction tells agents how to behave during work — formatting rules, commit conventions, tool usage. A policy declares intent, goals, boundaries, and constraints for a domain — what must be true about audio, networking, or security regardless of implementation. Policies never name specific tools, commands, paths, or current state. They define requisites and boundaries in dense prose so that any implementation satisfying the constraints is acceptable. When asked to write a policy, do not produce implementation documentation or reference guides — those are instructions or code, not policy.
</policy_versus_instruction>

<evergreen_instructions>
Instructions become stale when code changes. Write instructions that stay accurate without maintenance.

Pointers over copies: "Run the rebuild script" not "Run ./home/modules/system/scripts/rebuild".
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

- Is the description over 2 sentences or ~30 words? Cut it — every skill's description loads in every agent session.
- Does the body repeat what the frontmatter description already says? Remove it.
- Does any section belong to a different skill's responsibility? Tool skills document their own API only — workflow composition belongs in workflow skills.
- Are there hardcoded file paths, tokens, or environment-specific values that will go stale? Generalize to patterns or point to where the truth lives.
- Would a dense two-line prose replace a verbose example block without losing clarity? Prefer density.
- Does any content exist only because raw research data was fresh in context? Strip research artifacts — write from synthesized patterns, not from raw dumps.
- Does any section explain what code does? Remove it — the model reads code. Only keep what the model cannot infer: traps, non-obvious constraints, sync requirements, and "whys".
</skill_authoring_preflight>
