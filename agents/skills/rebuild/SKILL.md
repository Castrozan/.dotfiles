---
name: rebuild
description: Apply Nix configuration changes. Use when modifying .nix files, after flake updates, or when user asks to rebuild/apply dotfiles changes.
---

<announcement>
"I'm using the rebuild skill to apply configuration changes."
</announcement>

<prerequisite>
Nix reads from git index, not working tree. Stage all modified .nix files before rebuilding. Never use `git add -A` or `git add .` (may stage unrelated parallel work).
</prerequisite>

<execution>
Run `rebuild` — it auto-detects platform (NixOS vs standalone home-manager) and user. Sources nix-daemon.sh if needed. If `nix: command not found`, source `. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh` first.
</execution>

<timeout_trap>
Run rebuild in the background with short poll intervals. Never use process poll with timeout > 60000ms. A hung nix build can block for minutes — a single long poll eats the entire agent timeout budget and bricks the session. The rebuild output is verbose — use background execution and only check the final exit code + last few lines.
</timeout_trap>

<dry_run>
Validate configuration before applying by running `rebuild` with `--dry-run`. Catches syntax errors, missing imports, and evaluation failures without modifying the system.
</dry_run>

<platform_difference>
NixOS: Full system rebuild affecting services, kernel, boot. Home-manager is integrated as a module.
Home-manager standalone: User-level only — packages, dotfiles, user services.
The rebuild script handles detection automatically.
</platform_difference>

<troubleshooting>
Build fails with import error: file not staged (check git status). Attribute not found: module not imported in home.nix or configuration.nix. Unfree package: rebuild sets NIXPKGS_ALLOW_UNFREE=1. Rate limit: install home-manager locally. Wrong config: session-context User field must match flake configuration name.
</troubleshooting>
