<identity>
`chise` (hatori chise) is a NixOS desktop, user `zanoni`, built from this flake as the `.#chise` attribute. The alias resolves to a physical hostname in `private-config/machines.nix`, outside this repo.
</identity>

<stack>
NixOS owns the system and runs home-manager inside it, both from this flake. System config lives under `hosts/chise/` (the hardware scan, the machine configuration, the NixOS-system module). The user environment composes `home/base` under `home/linux` through `home/hosts/linux/chise.nix`. Personal-only overlays are layered at deploy time by a machine-local `/etc/nixos/flake.nix` wrapper that composes this flake with the private overlay as separate inputs, never committed here.
</stack>

<per_host_delta>
`hosts/chise/` holds the hardware-configuration scan and this machine's NixOS system definition, both inherently unique. Regenerate the hardware scan with `nixos-generate-config --show-hardware-config` after hardware changes; never hand-edit it.
</per_host_delta>

<apply>
Run `nixos-rebuild switch --flake .?submodules=1#chise` on the machine. A successful rebuild is the verification; there is no separate check step.
</apply>

<rules>
Keep machine-specific secrets and personal overlays in the machine-local wrapper, never in this repo. Derive cross-platform behavior from the `isNixOS`, `isDarwin`, and `hostname` specialArgs, not from the literal alias.
</rules>
