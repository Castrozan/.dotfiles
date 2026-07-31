---
name: housekeeping
description: Recurring housekeeping sweep of the dotfiles tree for standing rot nothing else catches: stale markers, dead code, orphaned files, instruction drift, convention debt, chronic infra traps, test gaps. Triggers the dotfiles-housekeeping workflow.
---

Recurring sweep that cleans the dotfiles repo of standing rot the diff-reviewer and the linters never see. Run the
`dotfiles-housekeeping` workflow: it scans each rot dimension over the whole tree, adversarially refutes every finding,
and returns a severity-ranked triage report. It writes nothing.

The gap is the job. Linters, validators, the repo-hygiene test, and the diff-reviewer already own most cleanliness, so
the sweep reports only what they leave uncovered; re-flagging owned ground floods the report until it is ignored, which
is the one failure mode that kills it.

The rot dimensions, their false-positive boundaries, and the exclusion list of ground already owned are defined in the
co-located workflow `dotfiles-housekeeping.js`, which is the single source of truth. Edit that file to tune what the
sweep scans or excludes; do not restate its dimensions or exclusions here, or the doc drifts from the text that actually
drives the agents.

The sweep also drains `~/.claude/knowledge-inbox.md`, the ungated capture file where a session appends a fact it learned
the hard way rather than stopping mid-task to file it properly. Nothing loads that file, so an entry is inert until
filed. For each entry, either write it into the knowledge file of the skill that owns its subject, into the owning
repository's own instruction file, or into `agents/core_rules/` when it is a rule rather than an observation, then
remove it from the inbox. Discard anything a competent agent would re-derive from the code in five minutes, anything
already covered, and anything that has since become false. The design this implements is
`home/base/claude/docs/agent-memory.md`.

Filing a fact means writing it into the knowledge file that sits beside the owning skill's definition, the same
router-plus-siblings shape every skill here already uses.
