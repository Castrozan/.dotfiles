---
block: skill-and-script
group: hands
provides: action, observable
needs: driver
---

### What it gives

A skill instruction plus a command-line script that performs one deterministic action, such as applying a bulk change or
sending a campaign, with dry-run, verify, and status subcommands.

### Use when

The action's predicate is exact, it repeats, or it touches production. A script is cheaper, repeatable, and reviewable,
and it never drifts the way a model step does.

### Instruction

Call the script, never reimplement its action inline. Run its dry-run first, keep a backup or resumable log for every
batch, and read its status subcommand as the observable that monitors and verifiers use.

### Harness

A skill directory with a packaged script; the same script serves every harness, and an MCP server can expose it.
