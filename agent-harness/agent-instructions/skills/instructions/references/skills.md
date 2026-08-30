<extension_decision>
Use a skill when the AI should auto-detect relevance, when workflow guidance and progressive disclosure help, and when
behavior depends on what the agent finds at runtime; use a script when the user wants explicit control over a simple
repeatable, template-based action with fixed inputs and outputs.
</extension_decision>

<skill_format>
Skills live under `skills/<name>/SKILL.md` in the instruction source and deploy to AI agents through home-manager. Name
each skill in lowercase kebab-case after its directory and provide a routing description. Keep
optional instruction chapters under `references/` and executable logic under `scripts/`; keep SKILL.md as the minimal
entry point. Use the XML and prose limits from the instructions SKILL.md for every instruction chapter.
</skill_format>

<skill_discovery>
Description drives discovery. Models match semantically, so embed synonyms in prose. Every skill description is injected
into every agent session; each word is a shared token tax across all interactions. Cap at 2 sentences, ~30 words (the
repo validator rejects above 35). Add "Do NOT use for..." only where a sibling skill creates real confusion. All trigger
information goes in the description, not the body.
</skill_discovery>

<router_pattern>
When a skill grows past one screen, move optional chapters into `references/<chapter-name>.md` and keep SKILL.md as a
router with one-line loading hooks. The router loads on every invocation; references load on demand. Keep triggers and
orientation in SKILL.md. Resolve each backticked `references/<chapter-name>.md` path from the owning skill root; never
use a repository-root or absolute path for a skill reference.
</router_pattern>

<hardskill_belongs_in_scripts>
Scripts and their '--help' output are the authoritative source for exact commands, flags, and syntax. Skills document
what scripts cannot express: silent failure modes, non-obvious ordering constraints, domain boundaries, and which things
must stay in sync. If a script's name and '--help' already tell the agent how to use it, the skill must not repeat that
information; when a skill wraps scripts, the body is traps and boundaries, not a reference card for the CLI surface. The
exception is genuinely non-obvious hard constraints where wrong syntax silently succeeds (branch naming formats, socket
paths that fail silently, staging rules that cause data loss), which earn their token cost because the agent cannot
discover them by running '--help' or reading source; the test is "would the agent silently produce wrong results without
this line?", and if no, cut it.
</hardskill_belongs_in_scripts>

<skill_authoring_preflight>
Before committing any SKILL.md, answer these; if any answer is "yes", revise first: 1) is the description over 2
sentences or ~30 words? cut it (loads in every agent session); 2) does the body repeat what the frontmatter description
already says? remove it; 3) does any section belong to a different skill's responsibility? move it; 4) are there
hardcoded paths, tokens, or environment-specific values that will go stale? generalize to patterns; 5) would dense
two-line prose replace a verbose example block without losing clarity? prefer density; 6) does any content exist only
because raw research data was fresh in context? strip the research artifacts; 7) does any section explain what code
does? remove it and keep only what the model cannot infer.
</skill_authoring_preflight>
