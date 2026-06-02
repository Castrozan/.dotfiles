<identity>
`rin` (toosaka rin) is a macOS laptop, user `lucas.zanoni`, built from this flake as the `.#rin` attribute. The alias resolves to a physical hostname in `private-config/machines.nix`, outside this repo, so reimaging or renaming the hardware never touches config.
</identity>

<stack>
nix-darwin owns the system, home-manager owns the user environment. The Mac baseline (input, dock, browsers, window manager, terminal, the `rebuild` command) comes from the shared darwin layer at `hosts/shared-darwin-configuration.nix` and `hosts/shared-darwin/`. The user environment composes `home/base` under `home/darwin` through `home/hosts/darwin/rin.nix`.
</stack>

<per_host_delta>
`hosts/rin/default.nix` carries only what kira must not also get: Tailscale installed as a Homebrew formula rather than a managed service. Put a setting here only when it is genuinely unique to rin; anything both Macs share belongs in the shared layer.
</per_host_delta>

<apply>
Run the `rebuild` command on the machine. It targets `.#rin` because the flake host attribute is substituted from the `hostname` specialArg at build time. A successful rebuild is the verification; there is no separate check step.
</apply>

<rules>
Never branch on the literal alias; derive behavior from the `isDarwin`, `isNixOS`, and `hostname` specialArgs. Keep one copy of every asset: a file byte-identical with kira is a refactor trigger, hoist it to the shared layer. The per-host file trending toward empty is the goal, not a smell.
</rules>
