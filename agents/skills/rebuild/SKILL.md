---
name: rebuild
description: Apply Nix configuration changes. Use when modifying .nix files, after flake updates, or when user asks to rebuild/apply dotfiles changes.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<announcement>
"I'm using the rebuild skill to apply configuration changes."
</announcement>

<prerequisite>
Nix reads from git index, not working tree. Stage all modified files before rebuilding: `git add specific-file.nix` for each changed file. Never use `git add -A` or `git add .` (may stage unrelated parallel work).
</prerequisite>

<simple_rebuild>
Default method: `./bin/rebuild` (or `~/bin/rebuild` after install). Auto-detects NixOS vs standalone home-manager, sources nix-daemon.sh if needed, handles backup naming.
</simple_rebuild>

<nix_not_found>
If `nix: command not found`: source the daemon profile first.
`. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh`
Then retry the rebuild command.
</nix_not_found>

<dry_run>
Validate configuration before applying:
NixOS: `nix build ~/.dotfiles#nixosConfigurations.zanoni.config.system.build.toplevel --dry-run`
Home-manager: `home-manager build --flake ~/.dotfiles#lucas.zanoni@x86_64-linux --dry-run`

Dry-run catches syntax errors, missing imports, and evaluation failures without modifying the system.
</dry_run>

<platform_difference>
NixOS (zanoni user): Full system rebuild with `sudo nixos-rebuild switch --flake`. Requires sudo. Affects system services, kernel, boot.

Home-manager standalone (lucas.zanoni user): User-level only with `home-manager switch --flake`. No sudo needed. Affects user packages, dotfiles, services.

Detection: Check `/etc/os-release` for `ID=nixos`. The bin/rebuild script handles this automatically.
</platform_difference>

<workflow>
1. Make .nix file changes
2. Stage changed files: `git add path/to/changed.nix`
3. Dry-run to validate: use appropriate command from <dry_run>
4. If dry-run passes, apply: `./bin/rebuild`
5. Verify changes took effect

On NixOS: Ask user to run rebuild manually (requires sudo). On home-manager standalone: Execute directly.
</workflow>

<troubleshooting>
Build fails with import error: Check file exists and is staged (`git status`).
Attribute not found: Verify module is imported in appropriate home.nix or configuration.nix.
Unfree package error: Check NIXPKGS_ALLOW_UNFREE=1 is set (bin/rebuild does this).
Rate limit errors: Install home-manager locally: `nix profile install nixpkgs#home-manager`.
</troubleshooting>
