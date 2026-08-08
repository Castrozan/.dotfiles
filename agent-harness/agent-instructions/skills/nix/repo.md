<stance>
Enforce patterns, not just suggest. When user proposes violation: 1) Explain WHY pattern exists. 2) Show CORRECT way. 3)
Only deviate if user explicitly accepts trade-off AND no alternative exists.
</stance>

<architecture>
`flake.nix` owns inputs. `repository/flake-assembly/outputs.nix` owns outputs: it names every host explicitly and
calls `nixos-machine-factory.nix` or `darwin-machine-factory.nix` once per host to build `nixosConfigurations.<alias>`
(full NixOS system, e.g. chise) and `darwinConfigurations.<alias>` (nix-darwin macOS, e.g. rin, kira). Adding a host
is one more explicit call; never reintroduce a host list, an attrset iteration or a `pathExists` directory scan, all
of which hide which hosts exist. A factory file is curried, taking the platform arguments at import and the per-host
ones at each call; `channels.nix`, `home-manager.nix` and `checks.nix` are single application and keep noun names.
Each machine factory builds its channels from its own system and threads `hostname` (the alias), `username`,
`isNixOS` and `isDarwin` through `specialArgs` / `extraSpecialArgs`.
</architecture>

<platform_detection>
`isNixOS`, `isDarwin`, and `hostname` (the alias) are injected via specialArgs / extraSpecialArgs. Consume as function
args: `{ isNixOS, isDarwin, hostname, ... }:`. Use `lib.mkIf` to guard. NEVER use `builtins.pathExists /etc/NIXOS` -
broken in pure flake evaluation.
</platform_detection>

<directory_organization>
machine-configuration/machines/shared-home-manager-core.nix - shared home-manager core every machine imports
machine-configuration/machines/shared-darwin-{home-manager,system-nix-darwin}.nix - the layer both macOS hosts share
machine-configuration/machines/<alias>/home.nix - per-machine home-manager entry point (IMPORTS ONLY)
machine-configuration/machines/<alias>/home/ - optional per-machine home-manager submodules
machine-configuration/machines/user-packages-<user>-home-manager.nix - per-user shared package set (used by
multiple machines)
machine-configuration/development/version-control/git-private-home-manager.nix - per-user git router (sources
private-configuration/machines/<hostname>/git-user.nix)
machine-configuration/network/ssh/ssh-private-home-manager.nix - per-user ssh router (sources
private-configuration/machines/<hostname>/ssh.nix)
machine-configuration/network/ssh/scripts/ - shared per-user ssh activation scripts
machine-configuration/<domain>/<capability>/ - a capability owning its nix modules, raw config,
scripts and tests; deployment mechanism is the file-name suffix (-nixos, -nix-darwin, -home-manager)
machine-configuration/machines/<alias>/system/ - machine-specific system config; NixOS retains
nixos-system.nix for per-user-on-the-host bits
secrets/*.age - agenix encrypted secrets
secrets/secrets.nix - public key mappings
private-configuration/ - private git submodule (work agents, company skills, identity docs)
agent-harness/agent-instructions/ - instruction surfaces and shared skills deployed to every AI tool
</directory_organization>

<rebuild_execution>
Use the rebuild capability (rebuild.md) - it has platform detection, commands, and troubleshooting.
</rebuild_execution>

<git_workflow>
Commit files first before rebuilds, nix reads from git index. NEVER git add -A or git add . Parallel work is going on
the repo. Always add each file you changed with git add FILE.
</git_workflow>

<package_channels>
pkgs: stable (check flake.nix for version)
unstable: nixos-unstable
latest: same as unstable, updated with nix flake update nixpkgs-latest but done daily.
DO NOT UPDATE THE FLAKES MANUALLY unless user specifically requests it.
</package_channels>

<anti_patterns>
Reject: config in home.nix (goes in module), packages via specialArgsBase (use inputs), secrets without pathExists
guard, scripts in random locations, hardcoded usernames, new file without import, rebuild without staging, git add -A,
committing directly, builtins.pathExists /etc/NIXOS for NixOS detection (use isNixOS specialArg).
</anti_patterns>

<delegation_to_expert>
Delegate to expert.md: Nix syntax/evaluation/lazy evaluation, derivations/overlays/complex expressions, module system
internals, debugging evaluation errors, Nix ecosystem tooling questions.
Handle directly: file locations in this repo, repository patterns/anti-patterns, module structure/import organization,
secrets workflow, rebuild failures and enforcing conventions.
</delegation_to_expert>

<script_packaging>
Python scripts are packaged via a module-level helper in scripts.nix (e.g. `mkSystemPythonScript`,
`mkMediaPythonScript`) that wraps `pkgs.writeText` + `pkgs.writeShellScriptBin` with `exec python3`. For scripts needing
shared libraries, the shell wrapper sets PYTHONPATH to the lib directory. For external deps, use
`pkgs.python3.withPackages`. Each module with scripts has a __tests__/ directory with conftest.py for sys.path setup.
Mock subprocess calls in tests, never call real system tools.
</script_packaging>

<relevant_skills>
/hyprland-debug: Use for Hyprland/Wayland debugging - theme switching, service crashes, display issues, DRM conflicts.
</relevant_skills>
