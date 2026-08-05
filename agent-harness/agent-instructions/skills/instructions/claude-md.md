<purpose>
CLAUDE.md files state policies, identity, and constraints that the agent must satisfy in every session in a given
directory. They load unconditionally into the agent's initial context, so every word is a permanent token tax for as
long as the file exists.
</purpose>

<policy_not_documentation>
CLAUDE.md states what must be true and why without prescribing implementations. A good policy survives complete
reimplementation of the system it governs.
</policy_not_documentation>

<structure>
Should follow the format of the instructions SKILL.md.
</structure>

<what_belongs>
Constraints the agent would otherwise violate, workflow sequences that must run in order, general domain boundaries, and
identity facts. Everything else either belongs in a skill (workflow-specific guidance that loads on demand) or in code
(project structure, naming conventions enforced by linters and code review).
</what_belongs>

<authoring_review>
For each policy line, ask: "if the implementation changes in six months, does this line still hold?" If no, move it into
the code itself, into a script's '--help', or delete it.
</authoring_review>
