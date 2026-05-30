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

<stale_fetcher_cache>
`rebuild` builds the flake through the git fetcher (`.?submodules=1`), which caches the resolved repo revision in `~/.cache/nix/fetcher-cache-v*.sqlite`. This cache can pin an OLD commit and keep building stale source even after you commit new changes — and `--refresh`, `--option eval-cache false`, and `--option tarball-ttl 0` do NOT dislodge it.

Symptom: `rebuild` exits 0 but the change is not live. `nix flake metadata '.?submodules=1'` shows the new source, yet the build bakes in old file content at an unchanged store path. Confirm the fetcher is stale:
```
nix eval --impure --raw --expr '(builtins.getFlake "git+file://'"$PWD"'?submodules=1").rev'
git rev-parse HEAD   # if these differ, the fetcher cache is stale
```
Fix — drop only the fetcher cache (NOT all of `~/.cache/nix`, which needlessly re-downloads inputs), then rebuild:
```
rm -f ~/.cache/nix/fetcher-cache-v*.sqlite*
rebuild
```
Verify a deploy landed by inspecting the installed artifact, not the exit code. The hyprland python scripts are `writeShellScriptBin` wrappers that `exec` a separate `<hash>-source.py`; grepping the wrapper for your change is a false negative. Resolve `~/.nix-profile/bin/<name>`, extract the `/nix/store/...-source.py` it execs, and grep that.
</stale_fetcher_cache>

<troubleshooting>
Build fails with import error: file not staged (check git status). Attribute not found: module not imported in home.nix or configuration.nix. Unfree package: rebuild sets NIXPKGS_ALLOW_UNFREE=1. Rate limit: install home-manager locally. Wrong config: session-context User field must match flake configuration name.
</troubleshooting>
