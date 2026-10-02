---
name: devenv
description: Enter a project's devenv shell, run commands, update its lock, or clear stale state. Use when a repository carries devenv configuration and needs its toolchain on PATH.
---

### Entering

`devenv shell` activates the environment interactively; `devenv shell -- <command>` runs one command and exits. Prefer
the second form in scripts and CI, where an interactive shell never returns.

### Container isolation

For checkouts beneath the configured workspace root, use `devenv-container exec <project> -- <command>` for bounded
commands or `devenv-container shell <project>` for a persistent session. Run an installed agent inside that session to
contain its helpers too. Containers share a checkout's environment and retain their own Nix store, home and dependencies;
`nix profile add --profile ~/.local/state/nix/profile nixpkgs#<package>` adds tools without changing the host.
Read `devenv-container --help` and the deployed
`~/.config/devenv-container/policy.json` for lifecycle commands and limits. Native macOS automation and rebuilds remain
outside this Linux environment.

### Updating trap

`devenv update` rewrites `devenv.lock`, and a newer version regularly breaks a project that was working, so update only
when something needs it. Recover by restoring the previous lock from git or copying a working one from another project.

### Cleaning

When a build fails for no visible reason, `rm -rf .devenv/ .devenv.flake.nix` drops the cached state and the next
`devenv shell` rebuilds it.

### Direnv

Never use direnv. It is unreliable here and costs more debugging than it saves; call `devenv shell` directly.
