---
block: main-short-loop
group: eyes
provides: watch
needs: driver, observable
---

# main-short-loop

### What it gives

The main agent polls the process on a short interval and acts on issues immediately, with no handoff between seeing and
acting.

### Use when

The main agent itself must react, as when babysitting a pull request or a deploy, and the run is short. Avoid it when
the event can be pushed by a monitor, or when the job must outlive the session.

### Instruction

Self-pace: wait briefly while things change and long while quiet, keep intervals under the prompt-cache lifetime or well
above it, compare each poll with the baseline and thresholds, act on a breach, and stop the loop yourself at the stated
exit.

### Pitfalls

Every quiet poll spends model tokens; session-scoped loops expire, skip missed fires, and fire only while the session is
idle.

### Harness

Claude Code loops and scheduled wakeups; the main agent's own loop elsewhere.
