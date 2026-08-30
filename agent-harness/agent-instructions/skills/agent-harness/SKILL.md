---
name: agent-harness
description: Debug and configure the Claude Code, Codex, or OpenCode harness instead of the project it edits. Use for settings, skills, hooks, model routing, transcripts, MCPs, session state, or tool-targeting failures.
---

<scope>
Treat the harness as runtime infrastructure, not application code. Use this when a setting, skill, hook, connector,
subagent, model, transcript, session, or tool target behaves differently from the configured source.
</scope>

<live_state_over_files>
Apply core `<evidence>` and `<completion>` while reading the declared source, running harness, process, and session. A
deployed file does not prove a harness loaded it, and a resumed session can retain state from before a rebuild. Compare
versions and live state before calling a documented behavior a defect.
</live_state_over_files>

<configuration_ownership>
Keep durable settings and instruction surfaces declarative. Preserve harness-owned mutable state where the deployment
model requires it, and restart a session only after its replacement is available. Use `agent-session` for a generic
restart or exit instead of assuming a harness-specific command.
</configuration_ownership>

<place_instructions_by_scope_and_authority>
Place a rule by who needs it and how long it must remain available. Core, including `<coding>`, owns universal
session-long defaults even when they activate only for one kind of work; repository context owns local facts and policy;
path-scoped rules own matching-file constraints; harness surfaces own harness mechanics; skills own bounded procedures.
Make every complementary source point to the canonical authority instead of restating it. Never leave behavior expected
across turns or compaction solely inside an on-demand skill, because it disappears outside that skill's loading window.
</place_instructions_by_scope_and_authority>

<separate_adherence_evidence_and_enforcement>
Treat instruction salience, behavioral evidence, and enforcement as separate controls. Put persistent behavioral
authority at its proper scope. Enforce it mechanically only when the forbidden state and material exceptions are precise
enough to avoid unacceptable false results; otherwise an edit-parsing hook becomes a conflicting policy engine. Use
evaluations to expose adherence regressions, not as proof that prose forces behavior.
</separate_adherence_evidence_and_enforcement>

<instruction_authority_diagnosis>
Before diagnosing or migrating duplicated, missing, stale, or wrong-horizon behavior, read
`references/instruction-authority.md` and trace the rule through live delivery before selecting its owner.
</instruction_authority_diagnosis>

<workflow_authoring>
Before authoring or reviewing a workflow that calls agents or models, read `references/workflows.md` and budget its
control flow.
</workflow_authoring>

<knowledge>
Read `references/knowledge.md` for harness-specific traps, including transcript locations, configuration roots, model
routing,
hook protocols, skill discovery, connector gates, and command anchoring.
</knowledge>
