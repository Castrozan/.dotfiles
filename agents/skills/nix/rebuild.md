<announcement>
"I'm using the nix skill's rebuild capability to apply configuration changes."
</announcement>

<prerequisite>
Nix reads from git index, not working tree. Stage all modified .nix files before rebuilding. Never use `git add -A` or `git add .` (may stage unrelated parallel work).
</prerequisite>

<execution>
Run `rebuild` — it auto-detects platform (NixOS vs standalone home-manager) and user. Sources nix-daemon.sh if needed. If `nix: command not found`, source `. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh` first.
</execution>

<timeout_trap>
Rebuilds from source (forks, custom packages) can take 10+ minutes. Follow the active-waiting pattern: redirect output to a file (`rebuild > /tmp/rebuild.log 2>&1 &`), then set up a `/loop` monitor that tails the log file to check concrete progress. Never pipe through `tail` in background — it buffers everything and produces empty output. Never poll with timeout > 60000ms — a single long poll eats the entire agent timeout budget and bricks the session.
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
