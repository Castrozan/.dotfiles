---
name: documentation
description: Documentation policies and standards. Use when creating, updating, or reviewing any documentation — READMEs, TESTING.md, inline docs, file headers, or doc-related PRs.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<principle>
Code documents itself through naming. Documentation exists only for what naming cannot express: architecture decisions, onboarding context, external integration details, and cross-cutting concerns that span multiple files.
</principle>

<never_write>
Directory trees, file lists, or structure snapshots. These go stale the moment a file is added or removed. If someone needs to know the structure, they read the filesystem — that is the source of truth. Never duplicate what the filesystem already shows.
</never_write>

<evergreen>
Documentation must stay accurate without maintenance. Reference patterns, not current state. Point to locations, not copies. Write "tests live in tests/" not a tree of every test file. Write "scripts follow the pattern in ~/.dotfiles/bin/rebuild" not a list of every script. If documentation requires updating every time code changes, it is written wrong.
</evergreen>

<naming_over_docs>
A well-named function needs no docstring. A well-named file needs no README beside it. A well-named directory needs no index. Long, descriptive, obvious names are the primary documentation system. Never abbreviate. If you find yourself writing a comment or doc to explain something, rename the thing instead.
</naming_over_docs>

<when_docs_are_needed>
Architecture decisions that affect multiple modules. Setup or onboarding steps that cannot be inferred from code. External API contracts or integration requirements. Non-obvious constraints from upstream dependencies. Migration guides for breaking changes. These are the only valid reasons to write documentation.
</when_docs_are_needed>

<format>
Dense prose over bullet lists. No filler phrases. No "This document describes..." preambles. Start with the content. Use headings only when sections are truly distinct. Markdown only. No generated badges, no status indicators that need updating.
</format>
