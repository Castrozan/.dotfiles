---
name: nix
description: Nix everything: language expertise (lazy eval, derivations, overlays, module system, flakes, agenix, cachix), applying config via rebuild, THIS dotfiles repo conventions (module layout, isNixOS, script packaging, secrets, channels), and Docker/Podman container management via the docker-manager script. Use for any .nix edit, rebuild, container lifecycle, or "where does this belong in the dotfiles" question.
---

Umbrella skill for Nix language expertise, rebuild workflow, this repository's conventions, and container management.
Each capability lives in its own file so only the relevant one loads into context. Project development shells are the
separate `devenv` skill.

For Nix language and ecosystem expertise: idiomatic expressions, lazy evaluation, derivations, overlays, module system
internals (mkIf, mkMerge, types), flake design, ecosystem tools (direnv, cachix, agenix); read `expert.md`.

For applying configuration changes: staging prerequisite, rebuild script, platform detection, timeout/active-waiting
pattern, troubleshooting; read `rebuild.md`.

For THIS dotfiles repository: architecture, NixOS detection, directory organization, git workflow, package channels,
anti-patterns, script packaging, when to delegate to Nix expertise; read `repo.md`.

For Docker/Podman container management: the docker-manager script wrapper, safety boundaries (ordering, volume data
protection), container state, exec, volumes, networking, logging, registry; read `docker.md`.

For traps that cost real debugging and leave no trace in the source: what the build cannot see, submodule deployment,
activation failures that report green, and platform-specific rebuild fallout; read `knowledge.md`. Read it before
concluding that a rebuild landed or that a change failed to deploy for an unknown reason.
