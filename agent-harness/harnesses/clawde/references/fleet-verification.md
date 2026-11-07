### A worker that runs in the tree it proves can void its own proof

A validation worker whose cwd is the checkout writes into the tree it is proving, and a redirect fires before the
command feeding it fails, so a broken command chain still leaves a file behind. The build then succeeds against a dirty
tree and the proof is worthless while still reading exit 0, so consume the dirty flag alongside the exit code and never
the code alone.

The defence is ordering inside the runner and is two lines: open the worker log at an absolute path under the state
directory, chdir there, then invoke the build, after which even a careless relative redirect lands outside the tree.
What hides the litter is that a 0-byte file at the repo root is untracked, so a porcelain status passing
`--untracked-files=no` calls the tree clean; check untracked explicitly.

Ordering protects cwd and not HEAD: any phase resolving the flake from the checkout rather than a pinned rev reads HEAD
at eval time, so a commit landing mid-validation reproves a different revision than the result file is named after.
Capture HEAD at worker start and compare at the end, and hold commits while such a phase is in flight.

### A process match that can match the matcher

Any pattern matched against process command lines must be written so it cannot match the command doing the matching.
Whether it does depends on how the harness wrapped that command rather than on intent. The same pattern self-matches in
one invocation and not the next on one machine. The failure is silent in both directions. On the kill side it terminates
your own shell instead of the worker. On the read side it counts your own shell as a live worker, so a finished detached
job reads as still running.

Write the bracket form, `validate-runner[.]py`, which cannot match itself and returns the identical result where the
naive pattern was already fine. Reading the matched command line rather than the pid count is what catches it after the
fact.

### A check you have only seen pass is untested

A verification whose success output does not depend on its measurement is not a verification. An unconditional ok line
prints beside the violation it was meant to catch. A checker pointed at a mistyped path reports a silence that reads as
clean. Make the success branch conditional on finding zero violations, and fail loudly on an unreadable target. Prove
the failure paths before trusting the passing case. Force them once by tightening the threshold until it fires and
aiming it at a nonexistent file.

### Which tree a prose edit lands in decides whether it owes an activation

A commit touching only prose is not automatically activation-free. Part of the instruction tree is materialized into the
system closure and part is read from the checkout at runtime. The skills tree is symlinked in from home-manager files
and so ships in a closure. The harness tree is reached by repo-relative path from an instruction file that is itself in
a closure, so its content is read live. Editing
`agent-harness/agent-instructions/skills/<skill>/references/knowledge.md` therefore owes a switch and editing
`agent-harness/harnesses/<harness>/knowledge.md` does not, confirmed on three machines across two platforms.

Resolve the wrapper toplevel and compare against the running system rather than assuming a docs commit changes nothing.
Do not use the toplevel the validation result records until you have checked that what it built is what deploys, which
no result file states. Where a wrapper flake sits between repo and deploy, that path is the revision-pinned bare build.
It is a different derivation that never equals the running system, so comparing the two answers a question about
neither.

A host where the comparison is valid is usually safe by the shape of its backend rather than by anyone having checked,
which is why the check belongs in the reader and not in the host. Pin the revision into the deployed flake instead, with
`nix eval --override-input dotfiles <repo>?rev=<sha>` against the wrapper, which answers for any revision without moving
the checkout.

### Pushing to a stewarded repo

The steward shares the same checkout and continuously rebases and pushes `main`, so local `main` routinely diverges
mid-session and the submodule is often dirty during a sync. Land a single commit through a detached worktree
cherry-picked onto `origin/main` and fast-forward push it, rather than reconciling a diverged history by hand and racing
the loop.

### The service cgroup is the whole shared server

The service cgroup is not the agent fleet. It holds the shared multiplexer server, so everything that server hosts is
accounted to it: the fleet, the steward, the human's interactive session, and every command that session launches, a
rebuild included. Read `/proc/self/cgroup` from an interactive pane and it names the clawde unit.

Any memory knob on that unit therefore throttles the human. A ceiling sized to the fleet's resting set starves the
rebuild that would deploy it. Moreover, `MemoryHigh` alone relocates pages into swap rather than reducing them. A
ceiling under the honest working set therefore trades a RAM shortage for a swap exhaustion and leaves the desktop worse
off. Size such a ceiling as a runaway backstop above the resting set plus a concurrent build, never as a daily throttle,
and never add `MemorySwapMax` while swap is already full, which converts throttling into OOM kills.

### A quota dead agent reads as healthy

An agent whose model has exhausted its quota is the hardest fleet failure to see, because every layer reports fine. The
supervisor finds a live wrapper, the watchdog finds a pane parked at its idle prompt, and the change gate keeps firing.
Each heartbeat submits cleanly and then dies inside the harness leaving an empty assistant turn. The only tell is a
banner in the pane's own status row, and opencode parks on one for days behind a retry countdown rather than failing the
turn.

So before suspecting the supervisor, the resume chain or the heartbeat driver, read the agent's pane wide enough to
catch that row and check the model's quota. A stack of submitted heartbeats with no replies under them is the signature.
A workspace whose HEARTBEAT and inbox stopped moving days ago confirms it. That row also wraps mid-word at the widths
agents really run at, splitting a marker like `esc interrupt` across four lines, so any indicator matched against it
must ignore whitespace or it misses a banner that is plainly on screen.

### Ci sandbox lacks pgrep

The nix build sandbox provides no `pgrep` on either platform, so any test that shells out to it fails the flake check on
both runners. Stub it in the unit `conftest.py` as an autouse fixture exiting non-zero with no output, which is pgrep's
genuine no-match behavior, rather than skipping the tests or reaching for the real binary.
