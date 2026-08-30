---
name: docs
description: Documentation standards for when a doc earns its place, what never to write, evergreen phrasing, and policy shape. Use when writing or judging a README, doc, or policy; for authoring AI instruction files read instructions.
---

<core_coding_authority>
Core `<coding>` owns code naming and comment behavior. This skill decides whether separate documentation is justified
and how to keep it useful without becoming a second coding-policy authority.
</core_coding_authority>

<never_write>
Directory trees, file lists, or structure snapshots go stale the moment something changes.
</never_write>

<evergreen>
Documentation must stay accurate without routine maintenance. Reference patterns, not current state. Point to locations,
not copies. Write "tests live in tests/" rather than a tree of every test file. Write "scripts follow the rebuild
pattern" rather than a list of every script. If documentation requires updating whenever code structure changes, it has
captured the wrong detail.
</evergreen>

<when_docs_are_needed>
Write separate documentation only for architecture decisions that affect multiple modules, non-obvious upstream
constraints, migration guidance for breaking changes, external integration details, or a pointer to authoritative
external documentation.
</when_docs_are_needed>

<policy_documentation>
A policy is not documentation of code; it states intent, goals, boundaries, and constraints that code must satisfy.
Define what must be true and why without prescribing an implementation. Keep policy dense and independent of current
state, specific tools, exact commands, and implementation details. Put policy in an instruction surface or mechanical
assertion that lies in the path of the work; a detached policy document silently rots outside that path.
</policy_documentation>

<format>
Use Markdown. Exclude generated badges and status indicators because they become stale. Let the `humanize` skill own how
the prose reads on its published channel rather than creating a second communication rulebook here.
</format>
