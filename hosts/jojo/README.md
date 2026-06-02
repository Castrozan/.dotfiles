<identity>
`jojo` is an Ubuntu work laptop, user `lucas.zanoni`, applied from this flake as the `.#jojo` homeConfiguration. The alias resolves to a physical hostname in `private-config/machines.nix`, outside this repo. This directory exists only as the per-machine hub: jojo has no system config here because we do not own its OS.
</identity>

<stack>
home-manager standalone is the only layer. There is no nix-darwin and no NixOS module; the OS is stock Ubuntu managed outside this repo, so `isNixOS` and `isDarwin` are both false. Everything we control composes `home/base` under `home/linux` through `home/hosts/linux/jojo.nix`, wired as a `homeConfigurations` entry in `flake/outputs.nix`.
</stack>

<per_host_delta>
`home/hosts/linux/jojo.nix` is an explicit module list, not a thin delta over a shared Linux profile, because a corporate-managed Ubuntu host needs network and vendor-agent workarounds (FortiClient, OpenFortiVPN, Sophos plugin disables) that no other machine wants. Add or remove jojo capabilities by editing that module list.
</per_host_delta>

<apply>
Run `home-manager switch --flake .#jojo` on the machine. A successful switch is the verification; there is no separate check step.
</apply>

<rules>
Assume no root and no system-level control: everything must activate as an unprivileged home-manager generation on an OS this repo does not manage. Never reach for a NixOS or nix-darwin option here. Derive cross-platform behavior from the specialArgs, not from the literal alias.
</rules>
