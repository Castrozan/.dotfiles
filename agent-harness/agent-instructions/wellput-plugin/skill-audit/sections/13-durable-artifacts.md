# Durable artifacts: sentence audit

Sentence IDs S64-S65. [Audit overview](../../skill-audit.md). [Full sentence review](../../skill-review.md#durable-artifacts).

## Section assessment

An artifact can have a different audience and lifespan from the chat reply, so an adapter is justified. Repeating the
general context inventory contributes little, while importing broad documentation restrictions introduces mismatches
with snapshots and ownership trees. The exporter also rewrites the reference into a verified overlong body line.
Separate scope questions from that minor mechanical defect.

Most useful content: recognizing the artifact audience and lifespan. Main repair: narrow imported defaults and check
generated policy formatting. See F05, F08, and F10.

## S64: Merge general context, retain artifact-specific judgment

> Include the goal, material constraints, current state, evidence, limits, and required action when the durable
> artifact's reader lacks them.

**Assessment:** The context inventory repeats S3 and S8 with 'current state' added. That state can be essential in a
dated audit but is a staleness liability in evergreen architecture or policy documentation. The qualifier about what the
reader lacks is helpful but does not distinguish these artifact types.

**Related:** S8 owns reader recovery; S65 imports evergreen documentation constraints; the instruction principles favor
intent over mutable implementation snapshots.

**Recommendation:** Reuse the reader contract. Add artifact-specific source, audience, or state only when the artifact's
purpose requires it, and identify a state snapshot as such.

**Principles:** Density; horizon; evergreen scope.

## S65: Narrow the imported artifact policy

> Read `[artifact writing](references/artifact-writing.md)` to decide whether the artifact earns its place, what must
> remain evergreen, and how its conclusion, supporting context, and headings serve distinct reader needs.

**Assessment:** The reference provides useful evergreen-writing guidance, but it also forbids directory/structure
snapshots and limits when separate documentation is allowed. Those broad defaults overlap with S23's ownership paths and
with a user's explicitly requested saved review. The exporter changes the source sentence and produces a verified
154-character body line, so portability also bypasses the local wrap standard.

**Related:** S23 is the ownership-tree case; S64 is the state-snapshot case; export_plugin.py copies the docs policy
wholesale and rewrites this sentence.

**Recommendation:** Export only the artifact guidance that belongs to Wellput, with an explicit user-request boundary.
Keep generated instruction formatting under the same mechanical checks as the canonical source.

**Principles:** Scope; portable ownership; formatting consistency.
