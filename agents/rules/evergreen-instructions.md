---
description: Writing agent/skill instructions that stay accurate as code evolves
alwaysApply: false
globs:
  - "agents/**/*.md"
  - "**/SKILL.md"
  - ".claude/**/*.md"
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

Agent and skill instructions become stale when code changes. Write instructions that stay accurate by following these principles.

## Core Principle: Pointers Over Copies

Static docs describe WHAT and WHY. Dynamic discovery provides HOW.

Wrong: "Run `agenix-edit secret.age` to edit secrets"
Right: "Edit secrets using the tool in bin/ that handles agenix encryption"

Wrong: "Packages are in nixos-25.11 (stable)"
Right: "Check flake.nix inputs for current channel versions"

## Technique 1: Document Patterns, Not Commands

Patterns rarely change. Command names, paths, and flags change frequently.

Wrong: "Run `./bin/rebuild` after changes"
Right: "Run the rebuild script in bin/ after changes"

Wrong: "Add import to users/<username>/home.nix"
Right: "Add import to the user's home.nix entry point"

## Technique 2: Reference Code Locations

Point to where truth lives. Agent will read current state.

Instead of documenting CLI flags:
"Check bin/rebuild --help for current options"
"See secrets/secrets.nix for the key format"
"Module structure defined in home/modules/ - follow existing patterns"

## Technique 3: Describe Intent, Discover Implementation

What the user wants to accomplish rarely changes. How to accomplish it evolves.

Wrong: "Use `lib.mkIf (builtins.pathExists ../../secrets/x.age)` for conditional secrets"
Right: "Guard secret references with existence checks - see existing modules for pattern"

Wrong: "description field MUST be single-line with \\n escapes"
Right: "description format requirements in agents/rules/claude-code-agents.md"

## Technique 4: Version-Independent Language

Avoid embedding versions, dates, or release names.

Wrong: "pkgs is stable (nixos-25.11)"
Right: "pkgs is stable, latest is bleeding-edge - check flake.nix for versions"

Wrong: "Claude 4.x follows precise instructions"
Right: "Current Claude models follow precise instructions"

## When Specifics Are Unavoidable

Some instructions require exact commands. When documenting these:
1. Keep them in ONE authoritative location
2. Other docs point to that location
3. Mark clearly as "verify current command before using"

Example: Core rebuild command lives in CLAUDE.md. Agents say "run rebuild script" not "run ./bin/rebuild".

## Self-Verification Instruction

When an agent's instructions describe HOW to do something, include:
"Verify current approach by checking [specific file/directory]"

This teaches agents to confirm before acting on potentially stale instructions.
