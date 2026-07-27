<when>
Read before writing implementation code, and before reviewing someone else's.
</when>

<one-reason-to-change>
One responsibility per unit. When describing a function needs "and", split it. When a name needs "manager", "helper",
"handler" or "util" to fit, the unit has no single job yet and the name is hiding that.
</one-reason-to-change>

<dry-applies-to-decisions-not-shapes>
Deduplicate a decision, never a resemblance. Two blocks that look alike but change for different reasons stay
separate, because extracting them welds two futures together and the next change has to tear them apart. Wait for the
third occurrence, then extract the rule rather than the lines.
</dry-applies-to-decisions-not-shapes>

<solid-in-practice>
Depend on the narrowest interface the caller actually uses, not the fattest one available. Extend by adding a case the
existing code never has to learn about, rather than editing the same switch in five files. A subtype that throws on a
method its supertype promises is a broken hierarchy, not a special case. Inject what varies, construct what does not.
</solid-in-practice>

<coupling-and-cohesion>
Measure a change by how many files must move together. Data that always travels as a group is a type that has not
been declared. A parameter list past three, a boolean argument that selects behavior, and a call reaching two levels
into another object are the same defect surfacing three ways.
</coupling-and-cohesion>

<function-shape>
Guard clauses instead of nested conditionals, and return early. No output parameters. Every branch returns the same
shape. An error carries what the caller needs in order to act, and a swallowed error is a bug you chose to write.
</function-shape>

<tests-lead-the-code>
For a bug, the failing test comes first and must fail for the stated reason before any fix exists. For a feature,
write the assertion that describes done before the code that satisfies it. A test that cannot fail is not a test. The
`test` skill owns the rest of the verification protocol.
</tests-lead-the-code>
