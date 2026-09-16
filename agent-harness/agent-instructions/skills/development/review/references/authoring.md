### Scope

Audit instruction-file changes against the `instructions` skill. Instruction files include SKILL.md and its references,
agent definitions, CLAUDE.md at any depth, and prompt strings passed to agent or team tools in the diff. Load the
`instructions` skill before checking every changed instruction file.

### Excluded mechanical rules

Do not re-report description word counts or unresolved reference paths because deterministic validators own them. Let
the `coding` skill own naming, staging, and commit format; let [compliance](compliance.md) own Python over Bash,
test-first, and local-first checks.

### Evergreen text

Reject hardcoded absolute paths, exact command syntax, version numbers, dates, or release names that will rot. Prefer
patterns and intent over literals, and pointers such as "the rebuild script" over copies.

### Code explanation

Keep only behavior an agent cannot infer by reading the underlying code or script. Reject sections that merely describe
what a script does or what a directory contains.

### Density and voice

Require imperative voice and remove filler such as "you should," "please consider," or "as a reminder." Prefer dense
prose for connected ideas within the instruction grammar enforced by the repository validator.

### Named failure modes

Require every "do not" or "never" line to name the concrete failure it prevents. Reject generic caution because it does
not tell the model how behavior must change.

### Frontmatter duplication

Reject body prose that restates the frontmatter description.

### Surface fit

Apply core [instruction placement](../../../../core-rules/core.md#instruction-placement). Core owns universal
session-long defaults; the nearest CLAUDE.md or AGENTS.md owns repository and path policy; harness surfaces own
mechanics; skills own bounded procedures; script help owns exposed reference-card content.

### Staleness vector

Treat each file path, command flag, validator threshold, and tool name as a future liability. Require its presence to be
justified or replace it with a pattern. Reject files that need editing whenever unrelated implementation changes.

### Output contract

Write one line per finding as `PASS: file - rule-number - evidence`, `FAIL: file - rule-number - evidence`, or `UNKNOWN:
file - rule-number - insufficient data`. Report only FAIL and UNKNOWN unless the caller requests full output.
