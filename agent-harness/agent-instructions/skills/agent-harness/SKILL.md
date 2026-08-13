---
name: agent-harness
description: Debug and configure the Claude Code, Codex, or OpenCode harness instead of the project it edits. Use for settings, skills, hooks, model routing, transcripts, MCPs, session state, or tool-targeting failures.
---

<scope>
Treat the harness as runtime infrastructure, not application code. Use this when a setting, skill, hook, connector,
subagent, model, transcript, session, or tool target behaves differently from the configured source.
</scope>

<live-state-over-files>
Read the declared source, then inspect the running harness, process, and session. A deployed file does not prove a
harness loaded it, and a resumed session can retain state from before a rebuild. Compare versions and live state before
calling a documented behavior a defect.
</live-state-over-files>

<configuration-ownership>
Keep durable settings and instruction surfaces declarative. Preserve harness-owned mutable state where the deployment
model requires it, and restart a session only after its replacement is available. Use `agent-session` for a generic
restart or exit instead of assuming a Claude-specific command.
</configuration-ownership>

<place-instructions-by-scope-and-authority>
Choose a surface by who needs the rule, when it must load, and how much authority it needs. Core owns universal
cross-harness judgment and routing; a harness surface owns its mechanics; repository context owns local facts and
policy; a skill owns on-demand domain procedure; path-scoped rules own constraints limited to matching files; command
hooks own deterministic lifecycle automation; permissions or the operating system own security and integrity
boundaries. Importance alone never promotes capability policy into core. A short core route can require loading the
owning skill before action, but keep the full policy in that skill rather than copying it across layers.
</place-instructions-by-scope-and-authority>

<separate-adherence-evidence-and-enforcement>
Treat instruction salience, skill routing, behavioral evidence, and enforcement as different controls. Prose can
improve adherence and an eval can expose regressions, but neither forces behavior. Add a deterministic hook only when
the forbidden state is mechanically decidable with acceptable false positives and explicit exceptions; otherwise the
hook becomes a second policy engine that disagrees with the skill. Prefer gating an action until its owning skill is
loaded, then test the resulting behavior. If violations persist and the predicate can be made precise, validate the
final artifact at Stop or CI rather than parsing every edit in flight.
</separate-adherence-evidence-and-enforcement>

<knowledge>
Read `knowledge.md` for harness-specific traps, including transcript locations, configuration roots, model routing,
hook protocols, skill discovery, connector gates, and command anchoring.
</knowledge>
