---
block: workflow-script
group: hands
provides: action
needs: driver
---

### What it gives

A fixed fan-out, pipeline, or maker-checker loop executed by a script runner, with no model choice between steps and
schema-typed outputs.

### Use when

The shape is known before the run and repeats. Avoid it across a human gate, because a started workflow takes no input;
split it into one run per gate.

### Instruction

Author the workflow with a call ceiling, typed outputs, and one run per segment between gates. Resume a failed run
instead of restarting it.

### Harness

Claude Code workflow scripts; elsewhere the main agent runs the same shape itself.
