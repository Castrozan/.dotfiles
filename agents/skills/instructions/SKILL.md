---
name: instructions
description: Authoring AI instruction surfaces - SKILL.md, agent definitions, CLAUDE.md policies, and subagent briefs. Use when writing or editing any file that instructs an AI.
---

<density>
Context over quantity. Minimal high-signal tokens. Imperative voice ("Do X" not "You should do X"). Challenge each paragraph: does it justify its token/context cost? Cut anything the model can infer from reading the source.
</density>

<xml_structure>
Wrap distinct concerns in long descriptive XML tags. Tag names act as section headings, improve retrieval and reference. Inside tags, dense prose, plain text, no formatting. When sequential steps is is needed, inline it like "1) text; 2) text; 3) text", or "x; y; z". Never custom line breaks. For inline code, paths, commands, or identifiers use backticks. No bold, no italics, no markdown headers, no code fences. If a tag truly needs multi-section content, split it into sibling tags with descriptive names instead of breaking the no-line-break rule.
</xml_structure>

<never_over_explain>
Instruct only non-obvious constraints, traps that cannot be hard fixed in scripts, reasons behind surprising direction choices.
</never_over_explain>

<evergreen>
A stale instruction is worse than no instruction. Every specific detail that will change is a future liability. Fix with: 1) pointers over copies ("run the rebuild script" not the absolute path); 2) patterns over commands (document what to do, not how and exact syntax if that does not matter); 3) intent over implementation (what the user wants rarely changes, how to accomplish it evolves).
</evergreen>

<name_the_failure_trap>
Add a "do not" line only when a concrete foot-gun exists and cannot be avoided with code. Name the failure "X silently succeeds with wrong syntax" or "Y leaks credentials when Z is unset".
</name_the_failure_trap>

<authoring_review>
You just used this skill, and now its reviewing it again? Do this: iterate each section and answer: would the model behave differently if this section were absent? If no, delete it. If yes, can the same behavior shift be achieved in fewer words? Density is not a stylistic preference; it is a cost control for every future session that loads this file.
</authoring_review>

<skill_writing>
For SKILL.md files (frontmatter, discovery, router pattern, when to extract logic to a script), read `skills.md`.
</skill_writing>

<claude_md_instructions>
For definitions of CLAUDE.md files per context and workspace, read `claude-md.md`.
</claude_md_instructions>

<subagent_briefs>
For one-off prompts passed to other agents, read `subagent-briefs.md`.
</subagent_briefs>

<memory>
For how we think about agent memory systems, read `memory.md`.
</memory>
