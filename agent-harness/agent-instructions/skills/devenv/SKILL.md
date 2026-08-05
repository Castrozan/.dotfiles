---
name: devenv
description: Project-level development shells with devenv - enter a shell, run one command inside it, update the lock, clear stale state. Use when a repository carries a devenv configuration and its toolchain has to be on PATH.
---

<entering>
`devenv shell` activates the environment interactively; `devenv shell -- <command>` runs one command and exits. Prefer
the second form in scripts and CI, where an interactive shell never returns.
</entering>

<updating_trap>
`devenv update` rewrites `devenv.lock`, and a newer version regularly breaks a project that was working, so update only
when something needs it. Recover by restoring the previous lock from git or copying a working one from another project.
</updating_trap>

<cleaning>
When a build fails for no visible reason, `rm -rf .devenv/ .devenv.flake.nix` drops the cached state and the next
`devenv shell` rebuilds it.
</cleaning>

<direnv>
Never use direnv. It is unreliable here and costs more debugging than it saves; call `devenv shell` directly.
</direnv>
