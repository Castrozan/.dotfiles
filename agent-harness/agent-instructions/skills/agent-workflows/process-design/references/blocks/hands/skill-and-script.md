---
block: skill-and-script
group: hands
provides: action, observable, artifact
needs: driver
---

# skill-and-script

### What it gives

A skill instruction plus a command-line script that performs one deterministic action, such as a bulk change or a
campaign send, with dry-run, verify, and status subcommands.

### Use when

A recurring procedure has exact steps or touches production; code is cheaper, repeatable, and reviewable, and it never
drifts the way a model step does. A rule every session needs belongs in always-loaded instructions, and an action that
must happen without exception belongs in a hook.

### Instruction

Call the script, never reimplement its action inline. Write the skill description as routing metadata saying what it
does and when, keep the body short with references one level deep, run the dry-run first, keep a backup or resumable log
per batch, and read the status subcommand as the observable that monitors and verifiers use.

### Pitfalls

Vague descriptions misroute; skills from untrusted sources can exfiltrate data; a side-effecting skill the model may
invoke on its own.

### Harness

The open Agent Skills format across Claude Code and Codex, with OpenCode reading skill directories; Claude Code can
disable model invocation for manual-only skills.
