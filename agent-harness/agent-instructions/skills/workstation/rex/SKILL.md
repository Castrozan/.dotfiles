---
name: rex
description: Use the rex CLI to manage Rex sessions, open tabs, arrange panes, run commands, inspect terminal output, and control connected Rex apps.
---

### Guide

Run `rex __internal skill --feature-session-naming=false` and follow the guide it prints. The installed Rex CLI writes
it, so it matches the running version. If that command fails, start with `rex whoami --json`, then `rex --help`.

### Configuration

Rex config is a read-only link deployed by the dotfiles `rex` module, and its agent skill and hook come from the
dotfiles harness. Change those owners and rebuild; `rex skill setup` and edits to `~/.config/rex` create drift.
