---
description: Instructions for autonomous execution mode (ia-work script)
alwaysApply: false
---

<mode>
Running without user interaction. No questions - make decisions.
</mode>

<nix_constraint>
All persistent config via ~/.dotfiles. Direct changes to non Nix-managed paths (~/.claude/*, ~/.config/*, /etc/nixos/*) are lost on rebuild. Workflow: modify ~/.dotfiles, verify with nix flake check, run rebuild (or leave for user if no sudo).
</nix_constraint>

<delegation>
Required. Config/file placement: @dotfiles-expert. Nix language/derivations: @nix-expert. Agents/skills/rules: @agent-architect. Do not implement directly in these domains.
</delegation>

<code_changes>
Use /worktrees for isolated work. Test in worktree, merge when complete.
</code_changes>

<decisions>
When ambiguous: minimal changes, existing patterns, document uncertainty.
</decisions>
