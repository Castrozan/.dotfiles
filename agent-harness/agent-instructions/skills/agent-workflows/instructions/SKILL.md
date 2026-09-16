---
name: instructions
description: Authoring AI instruction surfaces - SKILL.md, agent definitions, CLAUDE.md policies, and subagent briefs. Use when writing or editing any file that instructs an AI.
---

### Density

Context over quantity. Minimal high-signal tokens. Imperative voice ("Do X" not "You should do X"). Challenge each
paragraph: does it justify its token/context cost? Cut anything the model can infer from reading the source.

### Markdown structure

Write distinct concerns as sibling `###` headings followed by nonempty prose paragraphs. Use descriptive headings with
unique anchors. Keep each paragraph at or below six source lines, each section at or below 20 prose lines, and wrap
prose at word boundaries within 120 characters. Give each paragraph one idea. Insert blank lines at meaning boundaries,
keeping conditions and exceptions with the rule they qualify. The formatter preserves authored paragraph boundaries.

Use inline code for literals, paths, commands, identifiers, and format examples. Use inline Markdown links for section
references and skill chapters, resolved from the containing file; link to the owning file and its heading anchor. Keep
sequential steps inline as "1) text; 2) text; 3) text". The accepted body contains only headings, prose, inline code,
inline links, and soft wraps. Keep optional YAML mapping frontmatter outside the body, with each value on one line and
exempt from the prose wrap. Split a concern into sibling sections when it exceeds the section limit.

### File size

Keep each instruction file at or below 150 prose lines. Exclude blank lines, frontmatter delimiters and values, and
heading lines from that count. The repository's independent physical-file limit remains 200 lines.

### Never over explain

Instruct only non-obvious constraints, traps that cannot be hard fixed in scripts, reasons behind surprising direction
choices.

### Evergreen

A stale instruction is worse than no instruction. Every specific detail that will change is a future liability. Fix
with: 1) pointers over copies ("run the rebuild script" not the absolute path); 2) patterns over commands (document what
to do, not how and exact syntax if that does not matter); 3) intent over implementation (what the user wants rarely
changes, how to accomplish it evolves).

### Name the failure trap

Add a "do not" line only when a concrete foot-gun exists and cannot be avoided with code. Name the failure "X silently
succeeds with wrong syntax" or "Y leaks credentials when Z is unset".

### Authoring review

You just used this skill, and now its reviewing it again? Do this: iterate each section and answer: would the model
behave differently if this section were absent? If no, delete it. If yes, can the same behavior shift be achieved in
fewer words? Density is not a stylistic preference; it is a cost control for every future session that loads this file.

### Skill writing

For SKILL.md files, reference layout, discovery, routing, and script extraction, read [skills](references/skills.md).

### Claude md instructions

For definitions of CLAUDE.md files per context and workspace, read [claude md](references/claude-md.md).

### Subagent briefs

For one-off prompts passed to other agents, read [subagent briefs](references/subagent-briefs.md).

### Refining an existing file

To break an existing instruction file down sentence by sentence and refine it with the user, read
[refine](references/refine.md).
