---
name: codewiki
description: Regenerate AI-consumable codebase documentation after significant structural changes. Use when you added/removed modules, reorganized directories, or completed a large refactor.
---

<when_to_run>
Run after significant structural changes: added/removed nix modules, created new skills, reorganized directories, added scripts to bin/, changed schemas, or completed large multi-file refactors. Do not run for minor changes — docs are expensive to produce and small edits won't meaningfully change them.
</when_to_run>

<usage>
Full regeneration: run the generate script in the codewiki project directory targeting the repository path. Partial: use --focus with areas like modules, architecture. Auto-detect: use --diff to inspect git changes and regenerate affected docs only, or --diff-from REF for a specific branch. Dry run: --dry-run to pack and show size without generating.
</usage>

<document_types>
architecture (ARCHITECTURE.md): overview, tech stack, structure, component map, data flow. modules (MODULES.md): module index, dependency graph, public interfaces. database (DATABASE.md): schema, ER diagrams, migrations. api (API.md): endpoints, auth, request/response shapes. glossary (GLOSSARY.md): domain terms, naming conventions.
</document_types>

<output>
Docs written to docs/ai-context/ in the target repository with INDEX.md listing all available docs. Read INDEX.md before exploring source code.
</output>

<diff_based_regeneration>
The --diff flag maps changes to doc types: nix/module changes → architecture + modules, skill changes → modules + glossary, script changes → api + modules, schema changes → database, 20+ files → regenerate everything.
</diff_based_regeneration>
