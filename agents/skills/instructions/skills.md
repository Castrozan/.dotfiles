<extension_decision>
Use a skill when the AI should auto-detect relevance, when workflow guidance and progressive disclosure help, and when behavior depends on what the agent finds at runtime; use a script when the user wants explicit control over a simple repeatable, template-based action with fixed inputs and outputs.
</extension_decision>

<skill_format>
Skills live in 'agents/skills/<name>/SKILL.md' and deploy to AI agents via home-manager (drop a directory, the build picks it up). YAML frontmatter requires 'name' and 'description'. Short directory names for easy discovery. Body uses XML tags with dense prose per 'principles.md'. Script-backed skills keep logic in a 'scripts/' subdirectory with SKILL.md as a minimal entry point.
</skill_format>

<skill_discovery>
Description drives discovery. Models match semantically, so embed synonyms in prose. Every skill description is injected into every agent session; each word is a shared token tax across all interactions. Cap at 2 sentences, ~30 words (the repo validator warns above 35). Add "Do NOT use for..." only where a sibling skill creates real confusion. All trigger information goes in the description, not the body.
</skill_discovery>

<router_pattern>
When a skill grows past one screen, split sub-files by surface and keep SKILL.md as a router that names each sub-file with one-line hooks. The router loads on every invocation; sub-files load on demand. Move depth into sub-files, keep triggers and orientation in SKILL.md. The repo validator checks that every `' 'filename.md' '` reference in SKILL.md resolves to a real file in the skill directory.
</router_pattern>

<hardskill_belongs_in_scripts>
Scripts and their '--help' output are the authoritative source for exact commands, flags, and syntax. Skills document what scripts cannot express: silent failure modes, non-obvious ordering constraints, domain boundaries, and which things must stay in sync. If a script's name and '--help' already tell the agent how to use it, the skill must not repeat that information; when a skill wraps scripts, the body is traps and boundaries, not a reference card for the CLI surface. The exception is genuinely non-obvious hard constraints where wrong syntax silently succeeds (branch naming formats, socket paths that fail silently, staging rules that cause data loss), which earn their token cost because the agent cannot discover them by running '--help' or reading source; the test is "would the agent silently produce wrong results without this line?", and if no, cut it.
</hardskill_belongs_in_scripts>

<skill_authoring_preflight>
Before committing any SKILL.md, answer these; if any answer is "yes", revise first: 1) is the description over 2 sentences or ~30 words? cut it (loads in every agent session); 2) does the body repeat what the frontmatter description already says? remove it; 3) does any section belong to a different skill's responsibility? move it; 4) are there hardcoded paths, tokens, or environment-specific values that will go stale? generalize to patterns; 5) would dense two-line prose replace a verbose example block without losing clarity? prefer density; 6) does any content exist only because raw research data was fresh in context? strip the research artifacts; 7) does any section explain what code does? remove it and keep only what the model cannot infer.
</skill_authoring_preflight>
