### Purpose

CLAUDE.md files state policies, identity, and constraints that the agent must satisfy in every session in a given
directory. They load unconditionally into the agent's initial context, so every word is a permanent token tax for as
long as the file exists.

### Scope and authority

Apply core [instruction placement](../../../../core-rules/core.md#instruction-placement) before choosing this surface. A
CLAUDE.md owns repository or directory policy that every session in that scope needs. Keep universal session-long
defaults in core, harness mechanics at their harness boundary, bounded procedures in skills, and exact controls in code,
hooks, permissions, or CI.

### Policy not documentation

CLAUDE.md states what must be true and why without prescribing implementations. A good policy survives complete
reimplementation of the system it governs.

### Structure

Should follow the format of the instructions SKILL.md.

### What belongs

Put repository or directory constraints, ordered local workflows, domain boundaries, and local identity facts here when
every session in that scope needs them. Put discoverable structure and exact predicates in their mechanical owner, and
route operation-specific guidance to its skill.

### Authoring review

For each policy line, ask: "if the implementation changes in six months, does this line still hold?" If no, move it into
the code itself, into a script's '--help', or delete it.
