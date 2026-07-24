<stance>
Enforce patterns, not just suggest. When user proposes violation: 1) Explain WHY pattern exists. 2) Show CORRECT way. 3)
Only deviate if user explicitly accepts trade-off AND no alternative exists.
</stance>

<architecture>
flake.nix (inputs) + flake/{outputs,nixos-configurations,darwin-configurations,home-manager-modules}.nix (outputs)
  nixosConfigurations.<alias>          (full NixOS system, e.g. chise)
  darwinConfigurations.<alias>         (nix-darwin macOS, e.g. rin, kira)
Each output threads (hostname=<alias>, isNixOS, isDarwin, username) through extraSpecialArgs.
</architecture>

<platform_detection>
`isNixOS`, `isDarwin`, and `hostname` (the alias) are injected via specialArgs / extraSpecialArgs. Consume as function
args: `{ isNixOS, isDarwin, hostname, ... }:`. Use `lib.mkIf` to guard. NEVER use `builtins.pathExists /etc/NIXOS` -
broken in pure flake evaluation.
</platform_detection>

<directory_organization>
bin/ - standalone scripts (system-wide, executable)
home/core.nix - shared home-manager core
home/scripts/ - home-manager managed scripts (nix-built)
home/{base,linux,darwin}/ - shared modules (name.nix or name/default.nix for complex)
home/hosts/{linux,darwin}/<alias>.nix - per-machine home-manager entry point (IMPORTS ONLY)
home/hosts/{linux,darwin}/<alias>/ - optional per-machine home-manager submodules
home/base/packages/<user>.nix - per-user shared package set (used by multiple machines)
home/base/dev/git-private.nix - per-user git router (sources private-config/machines/<hostname>/git-user.nix)
home/base/network/ssh-private.nix - per-user ssh router (sources private-config/machines/<hostname>/ssh.nix)
home/base/network/scripts/ - shared per-user ssh activation scripts
nixos/modules/ - NixOS-only modules
hosts/<host>/ - machine-specific system config; nixos hosts also have nixos-system.nix for per-user-on-the-host bits
secrets/*.age - agenix encrypted secrets
secrets/secrets.nix - public key mappings
private-config/ - private git submodule (work agents, company skills, identity docs)
agents/ - AI agent instructions .md files (symlinked to AI tools configs)
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
