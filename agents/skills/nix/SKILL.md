---
name: nix
description: Nix everything — language and ecosystem expertise (lazy eval, derivations, overlays, module system, flakes, agenix, cachix), applying configuration changes via rebuild, project-level devenv shells, and the conventions of THIS Nix-based dotfiles repository (module layout, isNixOS detection, script packaging, secrets workflow, package channels). Use for any .nix edit, rebuild, devenv shell change, or question about where something belongs in the dotfiles.
---

Umbrella skill for Nix language expertise, rebuild workflow, devenv shells, and this repository's conventions. Each capability lives in its own file so only the relevant one loads into context.

For Nix language and ecosystem expertise — idiomatic expressions, lazy evaluation, derivations, overlays, module system internals (mkIf, mkMerge, types), flake design, ecosystem tools (direnv, cachix, agenix) — read `expert.md`.

For applying configuration changes — staging prerequisite, rebuild script, platform detection, timeout/active-waiting pattern, troubleshooting — read `rebuild.md`.

For project-level dev shells with devenv — entering, updating traps, cleaning stale state, why direnv is avoided — read `devenv.md`.

For THIS dotfiles repository — architecture, NixOS detection, directory organization, git workflow, package channels, anti-patterns, script packaging, when to delegate to Nix expertise — read `repo.md`.
