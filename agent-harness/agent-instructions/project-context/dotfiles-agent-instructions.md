---
description: Agent behavior instructions specific to the .dotfiles repository
alwaysApply: true
---

<orientation>
If you are reading this you are inside the dotfiles repo, the single declarative source of truth for every machine it
configures. The live machine is a projection of this repo, so its whole configuration - packages, services, host and
user settings, dotfiles, secrets, packaged scripts, even this instruction file - is produced by a nix module here and
materialized by a rebuild. A change made by hand on the running machine is drift the next rebuild erases; a change made
here is the real thing, which is why most tasks reduce to finding the module that already owns what you are changing and
editing that. Before guessing where something lives, load the `nix` skill: it carries this repo's map - module layout,
host split, secrets, script packaging, the "where does this belong" call.
</orientation>

<repo-local-skills>
`nix` and `agent-harness` are repo-local: both describe this tree, so they reach no global skill surface and instead
deploy into this repo's own project skill directories, gitignored exactly like the instruction file you are reading.
Claude and OpenCode load them automatically here. Codex discovers skills only under its own home, so read them in the
tree at `agent-harness/agent-instructions/skills/nix/SKILL.md` and
`agent-harness/agent-instructions/skills/agent-harness/SKILL.md`, each with a `knowledge.md` beside it.
</repo-local-skills>

<stewardship>
This repo is continuously kept synced, green, and pushed by an autonomous per-machine steward agent, declared in the
clawde-agents module and built from the clawde flake input where its behavior lives. You still push your own commits,
because CI is the test gate and a commit that never reaches origin is never verified, but push only what fast-forwards:
leave a diverged history, a rebase, or a submodule gitlink conflict to the steward rather than reconciling it by hand,
which races its live loop, unless explicitly told to act in the steward's place. A checkout that is ahead of, behind, or
diverged from origin/main is normal in-flight state the steward will reconcile; never surface it as a task pending on
the human.
</stewardship>

<configuration>
Every configuration change lives in this repo and applies declaratively through its capabilities - nix modules,
home-manager, agenix, overlays, packaged scripts - never by mutating a machine by hand outside the repo. Fold new config
into the existing module structure rather than adding one-off files. Make it work on every system type this repo targets
(NixOS and darwin) when the feature allows, guarding platform-specific pieces behind `isNixOS`/`isDarwin`. The same
holds across the harnesses this repo drives: reach Claude Code, Codex and OpenCode together, then Pi and Hermes
where each one supports the capability.
</configuration>

<nvim-keymaps>
Before suggesting, adding, or restoring any Neovim keybind, read and follow
`machine-configuration/editors/neovim/KEYMAPS_POLICY.md`: native Vim built-ins first, LazyVim conventions second,
custom maps only as a documented last resort, never shadowing a native key. Keep that file current whenever a binding
is added or removed on purpose; bindings it lists as removed stay removed unless the owner names one explicitly.
</nvim-keymaps>

<codex-managed-settings-ownership>
MCP servers are declared in nix at `agent-harness/harnesses/claude-code/mcps/default.nix` for Claude and
`agent-harness/harnesses/codex/config.nix` for Codex. Codex deploys an authoritative nix-source for managed settings,
including `mcp_servers`, then seeds a mutable
live config while preserving live entries in projects, marketplaces, and plugins. Declaratively sourced entries win on
key collisions, so an MCP dropped from its nix source disappears from the live config on the next rebuild.
</codex-managed-settings-ownership>

<machine-local-wrapper>
On chise only, the live system is not built straight from this repo: a machine-local entrypoint flake at
`~/zanoni-system` (outside this tree) imports the public chise config from here and layers a private overlay on top, and
`rebuild` builds that entrypoint, not this repo directly. So a service, unit, secret, or option that is live on chise
but absent from this repo is most likely owned by that overlay, not missing: check `~/zanoni-system` before declaring it
undeclared or re-adding it here. That entrypoint is its own standalone private git repo, with its own origin, not this
repo and not a submodule of it, no CI and no peer stewards; the chise steward keeps it reconciled with its origin
fast-forward-only, so commit a wrapper change into that repo rather than assuming a rebuild alone captures it.
Keep `~/zanoni-system` limited to private OpenClaw integration and secrets. Generic host, provider, and harness
configuration belongs in this repo; do not make public configuration depend on the private wrapper.
Chise-specific; other hosts build directly from this repo.
</machine-local-wrapper>

<scripts>
Python 3.12 is the default language for scripts. Use bash only when the script is a thin wrapper gluing shell-native
tools (tmux send-keys, fzf, sysctl pipelines) where Python would just be subprocess.run calls. Python scripts run via
Nix - no uv, no venv, no pip.

Only scripts under 10 lines of actual logic may live inline in `.nix` files via `pkgs.writeShellScript`,
`pkgs.writeText`, or similar builders. Anything longer goes to a dedicated file under the module's `scripts/` directory
and is referenced by path. Long inline scripts are unreadable, unformattable, untestable, and escape from nix string
interpolation rules destroys quoting. When in doubt, extract.
</scripts>

<testing>
Never present code that has not been rebuilt and tested. For .nix files, a successful rebuild IS the primary
verification. Do the local work first, through the rebuild and the manual tests the change calls for, and only then
push (see <workflow>). Pushing is what starts CI: it runs the script tiers and `nix flake check` on every push, and CI
is the test gate, so a local full-suite pass is not what proves a change. Reach for `repository/verification/run.sh`
only to reproduce a job CI turned red, or to iterate on a test you are writing. The same goes for a whole pytest tier
directory (`*/__tests__/unit`, `*/__tests__/integration`), bare `pytest`, `pytest agents`, `pytest .`, and `nix flake
check`: run a specific test file, or use `rebuild` as the local nix verification. Test every Neovim change live in a
newly created Herdr pane; automated and headless checks do not replace this manual test.
</testing>

<change-review-scope>
Run the packaged `dotfiles-change-review` command over your own commits before pushing a substantive change; every
harness runs it the same way, so never hand-roll a headless `claude -p` review. It anchors at the checkout your shell
sits in, so pass `--root <absolute checkout path>` whenever you work in a worktree, because the shell can start in a
sibling checkout and a review of the wrong one returns a clean tree that proves nothing. Commit first: this checkout is
shared, so a review of the working tree reads whatever peers left uncommitted, and a confirmed finding belongs in a
follow-up commit rather than an amend a peer may already have built on. A change is substantive when a wrong edit
would survive formatting and still change machine or agent behavior, a build, a deployment, a dependency, an
interface, a test, security, a secret, what this public repository exposes, or an operational instruction, or when
correctness depends on several files changing together. Skip the review only when every hunk is demonstrably
non-semantic, meaning a formatting or prose correction that alters no command, path, identifier, factual claim, policy
or behavior; review the whole change when substantive and non-substantive hunks are mixed or the classification stays
uncertain. Changed line and file counts never decide this, and skipping the review never excuses the rebuild or the
tests.
</change-review-scope>

<workflows>
Treat a workflow's model calls as delegation that consumes the task's agent budget, and keep every dotfiles workflow at
a fixed call ceiling with no per-item model calls. Author further dotfiles workflows as `dotfiles-*` under
`agent-harness/harnesses/claude-code/workflows/`, deployed to `~/.claude/workflows/`, rather than ad-hoc subagent
fan-out. Give each one a matching `dotfiles-*` command in `agent-harness/workflow-commands/`, because that command is
how every harness other than Claude Code reaches the workflow at all.
</workflows>

<workflow>
After editing any file in the dotfiles repo, execute this sequence before responding, no exceptions: 1) format edited
files; 2) stage each file with git add specific-file, never -A; 3) commit; 4) review the commits you just added when
they are substantive (see <change-review-scope>); 5) rebuild for any file change in this repo (see <rebuild>); 6) push,
which starts the run in the background; 7) do not block on the run: continue with the next independent piece of the
task while CI works, and check the verdict only when other work is exhausted and a response to the user is due - `gh run
list --commit $(git rev-parse HEAD) --json databaseId,name,conclusion` gives the run ids, then `gh run watch <id>
--exit-status` blocks on each until it finishes and exits non-zero when it ends red; a short sha matches no run and a
just-pushed commit has none for a few seconds, so pass the full sha and retry an empty list rather than reading it as
a verdict; 8) if the rebuild or CI fails: fix and repeat from 1; 9) only after a green rebuild and green CI: respond
to user. Every CI job reports all of
its failures rather than dying on the first, so read the whole run and fix the batch in one pass instead of pushing
once per error.
</workflow>

<applying-clawde-agent-changes>
A clawde agent's runtime config - heartbeat gate, interval, prompt, launch command, active hours, rotation - lives in a
per-agent file the wrapper re-reads on every restart, so a rebuild's warm redeploy applies config changes in place, no
respawn needed. The exception is a change to the agent-wrapper code itself: the running wrapper keeps executing the code
it launched with, so wrapper-code changes stay dormant until the window is fully respawned (reboot, or kill the window
so the supervisor recreates it from the new spec). Never assume rebuilt wrapper code is live on the running agents -
check the live process and respawn if it still runs the old code. Every other fleet trap that leaves no trace in the
source - resume identity, supervisor reconciliation, channel gating, the steward loop, the shared server cgroup - is in
`agent-harness/harnesses/clawde/knowledge.md`; read it before touching any agent, supervisor or heartbeat behavior.
</applying-clawde-agent-changes>

<agent-instructions>
The eval baseline (`agent-harness/quality/evaluations/baseline.json`) is a committed snapshot that CI guards via
`agent-eval --check-baseline` against absolute pass-rate floors and a relative regression gate that fails when the
overall pass rate drops more than a fixed margin below the previous committed baseline, and a freshness gate that fails
once the recorded
`generated_at` is older than the window in `run_evals_baseline.py`. Do not re-run `agent-eval --save-baseline` after
editing agent instructions; the full suite is a slow LLM run whose routing evals flake, so a proactive re-save bakes
transient failures into the committed baseline. Re-save only when `--check-baseline` fails CI, whether on a genuine
pass-rate regression or on staleness, or to deliberately record a meaningfully improved instruction surface.
</agent-instructions>

<herdr-server-restart>
herdr runs as one shared server, the `default` session, hosting the whole clawde fleet, the steward, and the interactive
session at once, so a new herdr binary from a rebuild only goes live on a full `herdr server stop` and relaunch, which
restarts every session on it and drops the whole fleet; the fleet self-heals as the clawde supervisor respawns agents
into their pinned sessions and the human reconnects with `herdr`. This restart is the normal way to apply a herdr change
and you complete it rather than handing it back, but it is fleet-wide and disruptive, so perform it only with the user's
explicit approval, current or prior, never unprompted, and when approved stop the server detached after a short delay so
your final report flushes before this session drops.
</herdr-server-restart>
