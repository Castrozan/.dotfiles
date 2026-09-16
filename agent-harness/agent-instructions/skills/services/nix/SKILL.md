---
name: nix
description: Use Nix language and ecosystem expertise, rebuild this dotfiles configuration, or manage Docker/Podman containers. Use for `.nix` edits, rebuilds, container lifecycle, or dotfiles placement.
---

### Scope

Umbrella skill for Nix language expertise, rebuild workflow, this repository's conventions, and container management.
Each capability lives in its own file so only the relevant one loads into context. Project development shells are the
separate `devenv` skill.

### Language expertise routing

For Nix language and ecosystem expertise: idiomatic expressions, lazy evaluation, derivations, overlays, module system
internals (mkIf, mkMerge, types), flake design, ecosystem tools (direnv, cachix, agenix); read
[expert](references/expert.md).

### Rebuild routing

For applying configuration changes: staging prerequisite, rebuild script, platform detection, timeout/active-waiting
pattern, troubleshooting; read [rebuild](references/rebuild.md).

### Repository routing

For THIS dotfiles repository: architecture, NixOS detection, directory organization, git workflow, package channels,
anti-patterns, script packaging, when to delegate to Nix expertise; read [repo](references/repo.md).

### Container routing

For Docker/Podman container management: the docker-manager script wrapper, safety boundaries (ordering, volume data
protection), container state, exec, volumes, networking, logging, registry; read [docker](references/docker.md).

### Debugging routing

For traps that cost real debugging and leave no trace in the source: what the build cannot see, submodule deployment,
activation failures that report green, and platform-specific rebuild fallout; read [knowledge](references/knowledge.md).
Read it before concluding that a rebuild landed or that a change failed to deploy for an unknown reason.
