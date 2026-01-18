---
description: Writing agent/skill instructions that stay accurate as code evolves
alwaysApply: false
globs:
  - "agents/**/*.md"
  - "**/SKILL.md"
  - ".claude/**/*.md"
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<principle>
Agent instructions become stale when code changes. Static docs describe WHAT and WHY. Dynamic discovery provides HOW.
</principle>

<pointers_over_copies>
Wrong: "Run agenix-edit secret.age to edit secrets"
Right: "Edit secrets using the tool in bin/ that handles agenix encryption"

Wrong: "Packages are in nixos-25.11 (stable)"
Right: "Check flake.nix inputs for current channel versions"
</pointers_over_copies>

<patterns_over_commands>
Patterns rarely change. Command names, paths, flags change frequently.

Wrong: "Run ./bin/rebuild after changes"
Right: "Run the rebuild script in bin/ after changes"

Wrong: "Add import to users/username/home.nix"
Right: "Add import to the user's home.nix entry point"
</patterns_over_commands>

<reference_locations>
Point to where truth lives. Agent reads current state.

Instead of documenting CLI flags:
"Check bin/rebuild --help for current options"
"See secrets/secrets.nix for the key format"
"Module structure defined in home/modules/ - follow existing patterns"
</reference_locations>

<intent_over_implementation>
What user wants rarely changes. How to accomplish it evolves.

Wrong: "Use lib.mkIf (builtins.pathExists ../../secrets/x.age) for conditional secrets"
Right: "Guard secret references with existence checks - see existing modules for pattern"

Wrong: "description field MUST be single-line with \\n escapes"
Right: "description format requirements in agents/rules/claude-code-agents.md"
</intent_over_implementation>

<version_independence>
Avoid embedding versions, dates, release names.

Wrong: "pkgs is stable (nixos-25.11)"
Right: "pkgs is stable, latest is bleeding-edge - check flake.nix for versions"

Wrong: "Claude 4.x follows precise instructions"
Right: "Current Claude models follow precise instructions"
</version_independence>

<unavoidable_specifics>
When exact commands required: keep in ONE authoritative location, other docs point there, mark as "verify current command before using". Example: core rebuild command lives in CLAUDE.md. Agents say "run rebuild script" not "run ./bin/rebuild".
</unavoidable_specifics>

<self_verification>
When instructions describe HOW: include "Verify current approach by checking [specific file/directory]". Teaches agents to confirm before acting on potentially stale instructions.
</self_verification>
