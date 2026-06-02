# Machines

Three named machines plus one home-only profile, all built from this single flake. Anime aliases (kira, rin, chise, jojo) key every configuration; the physical-hostname-to-alias map and per-machine role live in `private-config/machines.nix`, outside this repo, so reimaging or renaming hardware never touches config.

## What each is

- **kira, rin** are macOS laptops (nix-darwin + home-manager) under one user. Near-identical by design; they share everything except an irreducible per-machine delta.
- **chise** is a NixOS desktop (different user), system and home managed together.
- **jojo** is a standalone home-manager profile on a machine whose system we do not own.

## How one is assembled

A host resolves through `flake/<kind>-configurations.nix` into two halves: `hosts/<alias>/` for system config and `home/hosts/<platform>/<alias>.nix` for the user environment. specialArgs threads `username`, `hostname`, `isNixOS`, and `isDarwin` into every module, so platform branches and host-specific values are derived from args, never from a hardcoded alias.

Both halves layer the same way: a cross-platform base under platform-specific overrides. Home is `home/base` beneath `home/{darwin,linux}`. Darwin system config is `hosts/shared-darwin-configuration.nix` plus the modules under `hosts/shared-darwin/`, beneath the per-host file.

## Rules

- Anything two machines share lives in the shared layer. A per-host `default.nix` carries only what is genuinely unique to that machine; when it holds nothing else, that is the goal, not a smell.
- Never branch on a literal alias. Derive behavior from the specialArgs flags; when a host-specific value must reach a script, substitute it from `hostname` at build time (see the rebuild module).
- One copy of any asset. Files that are byte-identical across hosts get hoisted into the shared layer, code and docs alike.
- Apply with the `rebuild` command on the Macs or `nixos-rebuild` on chise. A successful rebuild is the verification; there is no separate "did it work" step.

## Why

Two almost-identical Macs make duplication the dominant failure mode, so the architecture optimizes for a single shared source of truth with a thin per-host override, and alias indirection keeps hardware identity private while letting one config follow a machine across reinstalls.
