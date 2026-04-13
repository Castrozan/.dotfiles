---
name: session
description: Session lifecycle and context preservation — deep work context management, workspace switching, git worktrees for parallel branches, tmux control for background processes, spawning interactive Claude Code instances via tmux or one-shot --print, end-of-work notifications to the user, session restart and exit.
---

Unified skill covering session management, context preservation, process control, parallel agent spawning, and user notification. Each capability lives in its own file so only the relevant one loads into context.

For deep work context management, read `deep-work.md`.

For workspace switching (between this repo and other directories), read `workspace.md`.

For git worktrees and parallel branches, read `worktrees.md`.

For tmux session and process control primitives, read `tmux.md`.

For launching new Claude Code sessions — interactive tmux windows, one-shot `--print`, builtin Agent/Team delegation, multiline prompt traps, resume-by-session-id — read `claude.md`.

For end-of-work notifications to the user (TTS, desktop popup, mobile push via ntfy), read `notify.md`.

For session restart, read `restart.md`.

For session exit, read `exit.md`.
