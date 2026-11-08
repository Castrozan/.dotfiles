---
name: state-machines
---

### Core state authority

Core [evidence](../../../../core-rules/core.md#evidence) and [coding](../../../../core-rules/core.md#coding) own
verification and code-quality defaults. This chapter owns the implicit state audit, its report, and the explicit design.

### What counts

An implicit state machine moves through distinct phases whose legal transitions no code models. Look for boolean flag
combinations, nullable fields used as markers, mode strings, and ordering between callbacks. Look for timers or async
tasks that imply a phase, retries, marker files, runtime state on disk, and service unit combinations. Conditions spread
across functions that together decide the phase count too.

### Audit procedure

Audit read-only: 1) find every flag, field, file, pending await and unit status the behavior reads; 2) name the phases,
including value combinations no code names; 3) cross every phase with every event, and treat each cell without a rule
as a suspect; 4) trace real commands or events into each suspect cell with `path:line` evidence; 5) reproduce it against
the real module in a scratch harness, and drop what you cannot trace.

### Traps worth checking

Check whether an async completion lands after a newer request, so the last request loses and a resource leaks. Check
counters or marker files that outlive their process, and shared cursors or locks that assume one consumer. Check
two-step transitions that fail halfway into the worse state. Check optional devices that invalidate mandatory state,
readiness checks blocked by stale failures of unused units, and expensive predicates re-run on every poll.

### Report template

Report each machine in risk order. Give its name and purpose, and where its state lives by `path:line`. Draw its states
and transitions as a small table or a mermaid `stateDiagram-v2`. List each illegal state with its triggering sequence,
marked reproduced or traced. Say whether making it explicit deletes code or removes a bug class, and what it touches.
Say plainly when a machine is fine as it is, and end with the number of machines found.

### Explicit design

Give each machine four parts in the module that owns it: 1) a phase type, an enum or frozen string object, never flags
or nullable markers; 2) one observe function that derives the phase; 3) a pure literal transition table read by one
decide function; 4) an apply edge that runs the decided effect without phase checks of its own.

Fill every cell of the table, keyed by phase then command or event. Give async work a request generation so stale
completions drop themselves. Order every two-step effect so a halfway failure lands in the benign state.

### Matrix tests

Check each table exhaustively in one test. Assert it covers every phase and command, and compare it to an expected
literal written in the test. A new phase or command then fails until someone decides its cells. Keep behavior tests for
the effects, and confirm each defect test fails on the old code first.
