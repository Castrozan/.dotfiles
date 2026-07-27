---
name: architecture
description: Boundaries, dependency direction, system design, UML and deployment shape. Use when choosing a structure, adding a module or service, moving a boundary, or reviewing a design.
---

<put-the-seam-where-the-reason-to-change-is>
Name the thing that changes for its own reason and cut there. Dependencies point inward toward the rules that outlive
them: domain logic knows nothing about the database, the framework, the transport or the UI, and every replaceable
thing sits behind an interface the domain owns rather than one the vendor shipped. A module that imports its caller is
a defect, not a style choice.
</put-the-seam-where-the-reason-to-change-is>

<size-the-design-to-the-evidence>
Build what the current requirement needs plus the seam where the next one is already known to land. An abstraction
with one caller is a guess; a duplicated decision with three callers is debt. Moving a boundary later costs less than
defending one chosen early, so prefer the structure that is cheap to cut again.
</size-the-design-to-the-evidence>

<decide-state-and-failure-before-the-happy-path>
Say where state lives, who is allowed to write it, and what the system does on partial failure, before designing the
success case. Idempotency, retry semantics and ordering guarantees are design decisions; deciding them after the
callers exist means rewriting the callers.
</decide-state-and-failure-before-the-happy-path>

<diagram-only-to-settle-something>
Reach for UML when it decides an argument: a sequence diagram for ordering and failure across components, a component
or class diagram for dependency direction, a state diagram for a lifecycle with illegal transitions. Draw it in the
message or the plan. A committed diagram goes stale and then lies.
</diagram-only-to-settle-something>

<deployment-is-part-of-the-design>
Decide what runs where, what it needs at boot, what happens on restart, how it is observed and how it rolls back. A
design that cannot be deployed or reverted is unfinished, and infrastructure discovered after the code is written
reshapes the code.
</deployment-is-part-of-the-design>

<defer-to-the-repo>
Naming, comment policy, module layout and scripting language are set by the core rules and the surrounding code. Where
this skill and the surrounding code disagree, the surrounding code wins.
</defer-to-the-repo>
