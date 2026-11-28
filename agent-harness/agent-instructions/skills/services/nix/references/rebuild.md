### Announcement

"I'm using the nix skill's rebuild capability to apply configuration changes."

### Prerequisite

Nix reads from git index, not working tree. Stage all modified .nix files before rebuilding. Never use `git add -A` or
`git add .` (may stage unrelated parallel work).

### Execution

Run `rebuild`; it auto-detects platform (NixOS vs standalone home-manager) and user. Sources nix-daemon.sh if needed. If
`nix: command not found`, source `. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh` first.

### Timeout trap

Rebuilds from source (forks, custom packages) can take 10+ minutes. Launch a long one detached with
`launch-command-detached-into-new-session <log> rebuild`, block on `wait-for-event process <printed pid>`, and read the
log once it exits rather than re-reading it while it runs. Never pipe through `tail` in the
background; it buffers everything and produces empty output. Never poll with timeout `>` 60000ms: a single long poll
eats the entire agent timeout budget and bricks the session.

### Rebuild contention

The rebuild lock rejects a second `rebuild` instead of queueing it and names its holder in the
`LOCKED_BY_CONCURRENT_RUN` output. Do not wait in line and do not compete for the lock: commit, push, and leave the
change for the next rebuild. Every rebuild builds the shared `main`, so one rebuild deploys every pushed commit; five
agents need one rebuild, not five. Rebuild yourself only when the lock is free and you need the result live to verify
your own work.

### Commit attribution

The `prepare-commit-msg` hook stamps every agent commit with an `Agent-Name` trailer, so a failed build maps to its
author. Never write the trailer by hand; the hook owns it.

### Failed build duty

The agent whose commit broke a build repairs it before anything else, so the lock frees for the others. Pick by cost: 1)
quick fix needing no full rebuild to confirm: fix forward and push; 2) fix needing its own full rebuild: `git revert`
your commit, push, and redo the change off `main`. Never repair or revert a peer's commit; message its author.

### Rebuild coordination

Coordinate over `a2a`: tell the lock holder when you push behind its running rebuild, tell peers when your commit broke
a build or you reverted it, and `a2a send` a failing commit's `Agent-Name` author the log path.

### Platform difference

NixOS: Full system rebuild affecting services, kernel, boot. Home-manager is integrated as a module. Home-manager
standalone: User-level only: packages, dotfiles, user services. The rebuild script handles detection automatically.

### Stale fetcher cache

`rebuild` resolves the flake via the git fetcher (`?submodules=1`), which caches the repo revision in
`~/.cache/nix/fetcher-cache-v*.sqlite` and can pin an old commit so the build keeps using stale source after you commit;
`--refresh`, `--option eval-cache false`, and `--option tarball-ttl 0` do not clear it. Symptom: `rebuild` exits 0 but
the change is not live and the built store path never changes; confirm by comparing `builtins.getFlake`'s `.rev` against
`git rev-parse HEAD`, a mismatch means the cache is stale.

Fix: `rm -f ~/.cache/nix/fetcher-cache-v*.sqlite*` then rebuild, deleting only this file and not all of `~/.cache/nix`
which forces needless input re-downloads.

Verify a deploy from the installed artifact, not the exit code: the hyprland python scripts are `writeShellScriptBin`
wrappers that `exec` a separate `<hash>-source.py`, so grep the `-source.py` the wrapper execs (the wrapper itself
silently lacks your change).

### Troubleshooting

Build fails with import error: file not staged (check git status). Attribute not found: module not imported in home.nix
or configuration.nix. Unfree package: rebuild sets NIXPKGS_ALLOW_UNFREE=1. Rate limit: install home-manager locally.
Wrong config: session-context User field must match flake configuration name.
