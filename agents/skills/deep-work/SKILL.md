---
name: deep-work
description: Context management for large multi-step work — preserves user prompts verbatim, maintains plans, and survives compactions and session jumps. Use when starting ambitious tasks that span multiple sessions or require prompt preservation.
---

<activation>
Activate when any condition is met: user says "big work" or similar, task has more than 5 discrete steps, work will clearly span multiple sessions, or user explicitly asks to preserve context. Do not activate for quick fixes, single-file edits, or tasks completable in one exchange. When in doubt, ask — the overhead of deep-work management on a small task wastes more than it saves.
</activation>

<workspace>
Create `.deep-work/{task-slug}/` in the project root. Add `.deep-work/` to `.gitignore` if not present. The workspace contains four files, each with a distinct purpose:

`prompts.md` — Every user prompt stored verbatim with timestamps. Never summarize, paraphrase, or omit. Copy the exact text. This is the single source of truth for what the user asked. After compaction, the original prompt is the only way to verify you haven't drifted from what was actually requested. When a user gives a detailed specification, requirements list, or multi-paragraph request, that text IS the requirements document — summarizing it destroys signal.

`plan.md` — The current implementation plan. Starts as initial breakdown, evolves as work progresses. Mark phases as done, in-progress, or pending. Update when approach changes — never let the plan diverge from reality. Include phase dependencies and ordering constraints so recovery knows what can be parallelized.

`progress.md` — Chronological journal of completed work. Each entry: timestamp, what was done, key decisions and their rationale, files changed. This reconstructs full context after compaction. Write entries in enough detail that a fresh agent with no conversation history can understand what happened and why.

`context.md` — Curated high-signal context that must survive compaction. Requirements extracted from prompts, constraints discovered during research, user corrections, non-obvious dependencies, architecture decisions. Not a dump — each entry must justify its inclusion by being something the agent cannot rediscover from reading code alone.
</workspace>

<update-cadence>
Write to disk at these moments: immediately when receiving a substantial user prompt, after completing each plan phase, when making a decision that changes the approach, before responding to the user after significant work. The cost of writing too often is near zero. The cost of losing context is starting over.
</update-cadence>

<recovery>
On session start or after compaction, if a `.deep-work/` workspace exists with active work, read all workspace files before doing anything else. Reconstruct understanding from: prompts.md for what was asked, plan.md for what's planned, progress.md for what's done, context.md for what was learned. Continue from where progress.md left off. Never ask the user to re-explain what's already captured in prompts.md.
</recovery>

<heartbeat-integration>
HEARTBEAT.md remains the lightweight signal that work is active. For deep-work tasks, HEARTBEAT.md points to the workspace directory so any agent or session knows where to find full context. HEARTBEAT.md says what and where; the workspace says everything else. Keep HEARTBEAT.md updated with current phase and workspace path.
</heartbeat-integration>

<compaction-survival-test>
Context compaction preserves system prompt and recent messages but discards earlier conversation. Everything not on disk is lost. Design your workflow assuming compaction can happen between any two messages. The litmus test: if all conversation history disappeared right now, could you continue from disk artifacts alone? If not, write more to disk before proceeding.
</compaction-survival-test>

<cleanup>
When work is delivered and confirmed complete, remove the workspace directory and clear HEARTBEAT.md. Do not accumulate stale workspaces. Workspaces older than 48 hours with no recent progress entries get reported to the user — do not silently resume or delete stale work.
</cleanup>
