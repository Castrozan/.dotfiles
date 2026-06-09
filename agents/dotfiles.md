---
description: Agent behavior instructions specific to the .dotfiles repository
alwaysApply: true
---

<stewardship>
This repo is continuously kept synced, green, and pushed by an autonomous per-machine steward agent (see the steward skill); git stewardship is the steward's job, not yours and not the human's. Commit your work, then stop: do not push, pull, rebase, fast-forward, force, or otherwise reconcile the checkout against origin - the steward does that on its heartbeat loop, validating green before every push, and a manual reconcile races it. A checkout that is ahead of, behind, or diverged from origin/main is a normal in-flight state the steward will reconcile; never surface it as a task pending on the human, and never resolve it by hand unless Lucas explicitly tells you to act in the steward's place.
</stewardship>

<configuration>
Every configuration change lives in this repo and applies declaratively through its capabilities - nix modules, home-manager, agenix, overlays, packaged scripts - never by mutating a machine by hand outside the repo. Fold new config into the existing module structure rather than adding one-off files. Make it work on every system type this repo targets (NixOS and darwin) when the feature allows, guarding platform-specific pieces behind `isNixOS`/`isDarwin`.
</configuration>

<scripts>
Python 3.12 is the default language for scripts. Use bash only when the script is a thin wrapper gluing shell-native tools (tmux send-keys, fzf, sysctl pipelines) where Python would just be subprocess.run calls. Python scripts run via Nix - no uv, no venv, no pip.

Only scripts under 10 lines of actual logic may live inline in `.nix` files via `pkgs.writeShellScript`, `pkgs.writeText`, or similar builders. Anything longer goes to a dedicated file under the module's `scripts/` directory and is referenced by path. Long inline scripts are unreadable, unformattable, untestable, and escape from nix string interpolation rules destroys quoting. When in doubt, extract.
</scripts>

<testing>
Never present code that has not been rebuilt and tested. For .nix files, a successful rebuild IS the primary verification. Run tests/run.sh (--nix when .nix files changed, --quick otherwise).
</testing>

<workflow>
After editing any file in the dotfiles repo, execute this sequence before responding. No exceptions.
1. Format edited files
2. Stage each file with git add specific-file (never -A)
3. Commit
4. Rebuild for any file change in this repo, running it yourself and never deferring to the user (see <rebuild>)
5. Run tests/run.sh
6. If rebuild or tests fail: fix and repeat from 1
7. Only after rebuild and tests pass: respond to user
</workflow>

<agent-instructions>
After editing agent instructions (any file under agents/ or any CLAUDE.md), run `agent-eval --save-baseline` before pushing so the compliance pass rate stays current.
</agent-instructions>
