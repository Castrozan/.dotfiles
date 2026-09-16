---
name: devenv
description: Enter a project's devenv shell, run commands, update its lock, or clear stale state. Use when a repository carries devenv configuration and needs its toolchain on PATH.
---

### Entering

`devenv shell` activates the environment interactively; `devenv shell -- <command>` runs one command and exits. Prefer
the second form in scripts and CI, where an interactive shell never returns.

### Updating trap

`devenv update` rewrites `devenv.lock`, and a newer version regularly breaks a project that was working, so update only
when something needs it. Recover by restoring the previous lock from git or copying a working one from another project.

### Cleaning

When a build fails for no visible reason, `rm -rf .devenv/ .devenv.flake.nix` drops the cached state and the next
`devenv shell` rebuilds it.

### Direnv

Never use direnv. It is unreliable here and costs more debugging than it saves; call `devenv shell` directly.
