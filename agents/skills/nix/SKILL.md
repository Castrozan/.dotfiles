---
name: nix
description: Nix everything — language expertise (lazy eval, derivations, overlays, module system, flakes, agenix, cachix), applying config via rebuild, devenv project shells, THIS dotfiles repo conventions (module layout, isNixOS, script packaging, secrets, channels), and Docker/Podman container management via the docker-manager script. Use for any .nix edit, rebuild, devenv shell, container lifecycle, or "where does this belong in the dotfiles" question.
---

Umbrella skill for Nix language expertise, rebuild workflow, devenv shells, this repository's conventions, and container management. Each capability lives in its own file so only the relevant one loads into context.

For Nix language and ecosystem expertise — idiomatic expressions, lazy evaluation, derivations, overlays, module system internals (mkIf, mkMerge, types), flake design, ecosystem tools (direnv, cachix, agenix) — read `expert.md`.

For applying configuration changes — staging prerequisite, rebuild script, platform detection, timeout/active-waiting pattern, troubleshooting — read `rebuild.md`.

For project-level dev shells with devenv — entering, updating traps, cleaning stale state, why direnv is avoided — read `devenv.md`.

For THIS dotfiles repository — architecture, NixOS detection, directory organization, git workflow, package channels, anti-patterns, script packaging, when to delegate to Nix expertise — read `repo.md`.

For Docker/Podman container management — the docker-manager script wrapper, safety boundaries (ordering, volume data protection), container state, exec, volumes, networking, logging, registry — read `docker.md`.
