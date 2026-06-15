---
description: Agent behavior instructions specific to the .dotfiles repository
alwaysApply: true
---

<stewardship>
This repo is continuously kept synced, green, and pushed by an autonomous per-machine steward agent (see the steward skill). Reconciling the checkout against origin - pull, rebase, fast-forward, reset, force, or merging origin/main into your work - stays the steward's exclusive job; doing it by hand races its live heartbeat loop and corrupts the in-flight reconcile, so never reconcile unless Lucas tells you to act in the steward's place. You need not wait for that heartbeat to land your own work: once your commit is green, push it via the fast-path that does not race the live rebase - cherry-pick your committed SHA onto origin/main inside a throwaway detached worktree, push that, then drop the worktree - never from the managed checkout, whose branch the steward rewrites live so a push from it is not a clean fast-forward. The commit object outlives a steward reset of main and the steward drops the duplicate by patch-id, so your direct push and the steward's both reaching origin is harmless. A checkout that is ahead of, behind, or diverged from origin/main is still normal in-flight state; never surface it as a task pending on the human.
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

<workflows>
For a substantive change to this repo, run the `dotfiles-change-review` workflow over the working diff before committing; it fans out one reviewer per dimension (correctness, nix rebuild safety, code style, instruction-surface quality, test coverage, public-repo safety) and adversarially verifies each finding. Author further repo workflows as `dotfiles-*` under `home/base/claude/workflows/`, deployed to `~/.claude/workflows/`, rather than ad-hoc subagent fan-out.
</workflows>

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

<applying-clawde-agent-changes>
A clawde agent's runtime config - heartbeat gate, interval, prompt, launch command, active hours, rotation - lives in a per-agent file the wrapper re-reads on every restart, so a rebuild's warm redeploy applies config changes in place, no respawn needed. The exception is a change to the agent-wrapper code itself: the running wrapper keeps executing the code it launched with, so wrapper-code changes stay dormant until the window is fully respawned (reboot, or kill the window so the supervisor recreates it from the new spec). Never assume rebuilt wrapper code is live on the running agents - check the live process and respawn if it still runs the old code.
</applying-clawde-agent-changes>

<agent-instructions>
The eval baseline (`agents/evals/baseline.json`) is a committed snapshot that CI guards via `agent-eval --check-baseline` against absolute pass-rate floors only - there is no age or freshness gate. Do not re-run `agent-eval --save-baseline` after editing agent instructions; the full suite is a slow LLM run whose routing evals flake, so a proactive re-save bakes transient failures into the committed baseline. Re-save only when `--check-baseline` fails CI on a genuine pass-rate regression, or to deliberately record a meaningfully improved instruction surface.
</agent-instructions>
