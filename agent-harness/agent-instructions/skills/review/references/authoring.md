<scope>
Audit instruction-file changes against the `instructions` skill. Instruction files include SKILL.md and its references,
agent definitions, CLAUDE.md at any depth, and prompt strings passed to agent or team tools in the diff. Load the
`instructions` skill before checking every changed instruction file.
</scope>

<excluded_mechanical_rules>
Do not re-report description word counts or unresolved reference paths because deterministic validators own them. Let
the `coding` skill own naming, staging, and commit format; let `references/compliance.md` own Python over Bash,
test-first, and local-first checks.
</excluded_mechanical_rules>

<evergreen_text>
Reject hardcoded absolute paths, exact command syntax, version numbers, dates, or release names that will rot. Prefer
patterns and intent over literals, and pointers such as "the rebuild script" over copies.
</evergreen_text>

<code_explanation>
Keep only behavior an agent cannot infer by reading the underlying code or script. Reject sections that merely describe
what a script does or what a directory contains.
</code_explanation>

<density_and_voice>
Require imperative voice and remove filler such as "you should," "please consider," or "as a reminder." Prefer dense
prose over lists for connected ideas; use a list only for genuinely unordered, disconnected items.
</density_and_voice>

<named_failure_modes>
Require every "do not" or "never" line to name the concrete failure it prevents. Reject generic caution because it
does not tell the model how behavior must change.
</named_failure_modes>

<frontmatter_duplication>
Reject body prose that restates the frontmatter description.
</frontmatter_duplication>

<surface_fit>
Apply core `<instruction_placement>`. Core owns universal session-long defaults; the nearest CLAUDE.md or AGENTS.md owns
repository and path policy; harness surfaces own mechanics; skills own bounded procedures; script help owns exposed
reference-card content.
</surface_fit>

<staleness_vector>
Treat each file path, command flag, validator threshold, and tool name as a future liability. Require its presence to be
justified or replace it with a pattern. Reject files that need editing whenever unrelated implementation changes.
</staleness_vector>

<output_contract>
Write one line per finding as `PASS: file - rule-number - evidence`, `FAIL: file - rule-number - evidence`, or
`UNKNOWN: file - rule-number - insufficient data`. Report only FAIL and UNKNOWN unless the caller requests full output.
</output_contract>
