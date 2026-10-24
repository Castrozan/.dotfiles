---
block: main-short-loop
group: eyes
provides: watch
needs: driver, observable
---

### What it gives

The main agent polls the process on a short interval and acts on issues immediately, with no handoff between seeing and
acting.

### Use when

The process is short, the signals are few, and reaction time matters more than tokens. Avoid it for long runs, where
every quiet poll spends model tokens and floods the main context.

### Instruction

Poll the observables at a fixed cadence, compare them with the baseline and thresholds, act on a breach, and stop
polling at the stated exit.

### Harness

Scheduled wakeups or a loop command in Claude Code; the main agent's own loop elsewhere.
