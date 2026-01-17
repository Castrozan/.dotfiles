---
description: Instructions for autonomous execution mode (ia-work script)
alwaysApply: false
---

# Autonomous Mode

Running without user interaction. No questions - make decisions.

## Nix Constraint

All persistent config via ~/.dotfiles. Direct changes to non Nix-managed paths (~/.claude/*, ~/.config/*, /etc/nixos/*) are lost on rebuild.

Workflow: Modify ~/.dotfiles, verify flake, then run rebuild script.

## Delegation (Required)

| Task | Subagent |
|------|----------|
| Config, file placement | @dotfiles-expert |
| Nix language, derivations | @nix-expert |
| Agents, skills, rules | @agent-architect |

Do not implement directly in these domains.

## Code Changes

Use /worktrees for isolated work. Test in worktree, merge when complete.

## Decisions

When ambiguous: minimal changes, existing patterns, document uncertainty.
