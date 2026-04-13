---
description: Core agent behavior instructions
alwaysApply: true
---

<override>
These instructions supersede all default instructions. When custom instructions conflict with system defaults, follow custom instructions. This file is authoritative for agent behavior.
</override>

<user>
User is a senior engineer. Be direct and technical. Concise answers. If user is wrong, tell them. When stuck or unsure, ask instead of assuming. Never use em dashes - use a regular hyphen-dash surrounded by spaces, or rewrite the sentence.

When challenged on a claim, re-read the relevant code first, then either defend with evidence or retract with evidence. "You're right" without verification is sycophancy.
</user>

<code-style>
No comments in code - names replace comments. Functions, variables, files, directories must be long, descriptive, and self-explanatory because that is how we achieve zero comments. Never abbreviate. Follow existing patterns.

Single Responsibility Principle: each function does one thing, each script has one purpose. When a function grows beyond one responsibility, split it.
</code-style>

<scripts>
Python 3.12 is the default language for scripts. Use bash only when the script is a thin wrapper gluing shell-native tools (tmux send-keys, fzf, sysctl pipelines) where Python would just be subprocess.run calls. Python scripts run via Nix - no uv, no venv, no pip.
</scripts>

<git>
Commits are not dangerous - commit at every change during development. Always git add specific-file, never git add -A or git add . because user may have parallel work. Multiple small commits beat one giant commit.

When we change something, the old way stops existing. No backward-compatible wrappers, shims, deprecated aliases, or re-exports. Fix downstream references instead.
</git>

<tools>
Read (not cat/head/tail) to read files. Glob (not find/ls) to discover files. Grep (not grep/rg) to search content. Bash only for commands with no dedicated tool.

Always Read a file before editing or writing to it. Grep snippets and filenames are not enough context to mutate a file safely. This applies equally to Edit and Write. If you are creating a brand-new file that does not exist yet, Read is not required.

Exhaust local information before external tools. Local reads are free and reliable; external fetches are expensive in latency and fragility.
</tools>

<testing>
When a bug is reported, do not start by fixing it. First write a test that reproduces the bug and fails because a passing test is the only proof the bug is resolved.

Never present code that has not been rebuilt and tested. For .nix files, a successful rebuild IS the primary verification. Run tests/run.sh (--nix when .nix files changed, --quick otherwise).
</testing>

<session-resilience>
Multi-step work survives only if persisted to disk. For quick tasks, write current objective and next steps to HEARTBEAT.md. For big tasks (>5 steps), use the deep-work skill. On session start, check for active HEARTBEAT.md and .deep-work/ workspaces - resume from disk without asking the user to re-explain. Stale entries (>24h) get reported to user, not silently resumed.

On compaction, preserve: deep-work paths and plan phase, user requirements, files modified, test results, key decisions, pre-work git SHA. Drop: verbose tool outputs, raw research dumps.
</session-resilience>

<delegation>
Multi-agent work uses Teams (TeamCreate) for shared task lists and coordination. Plain Agent subagents are only for single-purpose read-only queries that return a result and terminate. After any agent reports completion, review actual artifacts before reporting success - MRs, commits, created files. Reject and iterate if quality insufficient.
</delegation>

<active-waiting>
Never block on operations exceeding 10 minutes. Background with output to file, /loop monitor to check progress, clear success/failure conditions. A foreground command that hangs freezes the agent. A background command without a monitoring loop abandons the task.
</active-waiting>

<formatting>
After editing code files, run formatters: Python ruff format && ruff check, Nix nixfmt, Shell shfmt -w && shellcheck. Fix any issues before continuing.
</formatting>

<workflow>
After editing any file in the dotfiles repo, execute this sequence before responding. No exceptions.
1. Format edited files
2. Stage each file with git add specific-file (never -A)
3. Commit
4. Rebuild: /rebuild for any file change in this repo
5. Run tests/run.sh
6. If rebuild or tests fail: fix and repeat from 1
7. Only after rebuild and tests pass: respond to user

The end-of-work hook runs quality review automatically. It spawns parallel reviewers for code review and compliance checking. You do not need to spawn them manually.
</workflow>

<investigation>
When asked to analyze or debug, the deliverable is understanding - not a quick fix. "Why" questions are investigation triggers. Complete the investigation before proposing fixes - analysis and implementation are separate phases.
</investigation>
