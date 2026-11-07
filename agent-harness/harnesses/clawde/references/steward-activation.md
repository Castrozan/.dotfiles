### Steward loop

A submodule divergence verdict is returned before every other verdict and short-circuits the whole loop. The steward
therefore keeps ticking and pushes nothing no matter how green CI is. The recoverable shape is now rebased
automatically, and only a genuine gitlink-versus-gitlink conflict still needs a human.

The steward defers when it reads recent commits as the operator working, but peer agents commit under the same identity.
On a busy fleet the quiet window therefore never arrives. Unblock it through its inbox rather than by loosening its
caution. A growing unpushed chain is usually that same learned caution ratcheted incident by incident, not a broken
verdict.

Its health probe is capped at sixty seconds and reports the timeout exit as a parse error, which trains it off its own
primary tool. Adding a single verdict is shotgun surgery across five code sites plus four instruction tags, so budget
for that before proposing one.

### Self activation is written for systemd and records only its successes

The activation helper refuses to launch on darwin before doing any work. Its entry point exits when `systemd-run` is
absent, and its worker drives `systemctl --user`. The self-activation step is therefore dead on every darwin machine,
and only the linux one can use it as shipped. Reach the same code through its detached-worker entry point under a detach
the platform actually has, a double `fork()` plus `os.setsid()` from a granted pane. That also keeps the switch alive
when the pane dies mid-activation. The refusal is the launcher being linux-shaped, never the machine being ineligible.

Two traps sit behind that gate and bite only once a steward really is the activator. Health is sampled immediately after
the switch with no settle delay and no retry. Any label that passed before and fails after counts as a regression. A
service still coming up therefore reads as one and arms the rollback. That rollback is gated on the host being NixOS and
so is live on exactly one machine. That is the one where the operator rebuilds by hand within minutes of each commit,
which is why that rollback has never once executed. Whether the transition is rare is a question about which AGENT a
probe names, not about load, and the difference decides whether a machine is at risk.

### Post-switch responsiveness

Measured across eight consecutive validations on the linux machine, one agent's pane-responsiveness probe failed every
single time in the post-build health sample while its own liveness probe stayed green, and it passed in every standalone
health-check between them. That looks like load until the same sample is read whole: the two sibling agents'
responsiveness probes pass in that identical sample, at the same instant under the same build, so load is shared and
cannot be what separates them.

The agent that fails is the odd one by class. It is a gate-launched one-shot running a non-interactive `exec` turn
rather than a warm interactive session like the two that pass. That is the difference to suspect first when only one
probe of a kind misbehaves. What survives is narrow and still serious: one agent on one machine reliably presents the
pass-then-fail pair, and that machine is the one where the rollback is armed.

### Activation record and closure identity

And the last-activated record is written on the success path alone, so a failed or rolled-back activation leaves it
naming the previous revision: it is wrong in precisely the case you consult it. Audit an activation by store path
instead, comparing `/run/current-system` before and after against the closure the validating build produced. Read the
record as a claim rather than evidence. `/run/current-system` disagreeing with `/nix/var/nix/profiles/system` means the
switch aborted after the profile advanced.

That audit carries an ordering constraint worth holding, because losing it costs the evidence rather than the machine.
Every host whose build resolves the stewarded repo through a `git+file` reference has it. That reference is either a
wrapper flake taking the checkout as an input, or the checkout itself, which is the darwin backend's form. Resolving the
flake's toplevel answers for whatever the checkout holds right now. The one-command check therefore exists only while
the checkout sits on the revision in question. It returns a different closure the moment you sync.

On the direct form it is sharper still, since a lockless `git+file` reads tracked working-tree content rather than HEAD,
so an uncommitted edit moves the answer without any sync at all. Capture the live closure's identity before moving the
checkout, never after, or attributing a generation somebody else activated needs an explicit input override to
reproduce.

### A post switch regression costs the record even where it cannot roll back

Off NixOS the rollback is not merely gated, it is skipped outright with a null exit code and a line saying automatic
rollback is unavailable, which reads like the trap being harmless there. It is not, because the regression branch
returns before the last-activated write is reached, so nothing is ever stamped. The outcome on such a host is that the
switch succeeds and stays live, the result records a regression, and the record still names the previous revision: a
successful activation filed as a failure.

The two defects are one chain rather than two neighbours, since the health trap is what triggers the ledger trap, and
what it costs is exactly the evidence a later steward consults to decide what is running. Audit by store path and the
chain is visible; trust the record and it is invisible.

Whether a given clean activation is evidence at all turns on which probes were actually sampled. An agent-responsiveness
probe whose applicability gate is tied to that agent's active hours skips outside them, and a skipped probe presents no
pass-then-fail pair, so an after-hours run tells you nothing about a gated probe whatever the code does.

It does not follow that the host is untested, because gating is per agent rather than per host and one machine routinely
carries both kinds. An ungated probe sitting green on both sides of the switch is real evidence. It is evidence from the
worst possible window.

Enumerate the probes that ran before drawing either conclusion. Enumerate them from a full probe listing rather than
from a status summary. A summary that reports failures and skips never reports what quietly passed. Reading one as an
inventory is how a live ungated probe goes unnoticed.

Measured across three machines the load-deterministic failure appears on one agent's probe on one host and on no other.
Treat it as a property of the agent being probed until some second agent reproduces it. Never treat it as a property of
the platform or the hour.

### A verdict that cannot tell reports all clear

The steward's divergence count comes from asking git for a remote branch name. That name is built by concatenating
`origin/` with the branch it believes it is on, never by resolving the configured upstream. Both failure paths return
zero behind and zero ahead. A second route reaches the same place: the branch helper returns the literal string
`unknown` when `rev-parse` fails, and that interpolates into the same name, so a detached HEAD asks for `origin/unknown`
and lands on the identical zero.

Either way "cannot determine" is published as "no divergence", which is worse than an error, because a steward reading
zero behind stops looking; it recurred four times on one machine before anyone caught it. Guarding the concatenation
alone leaves the second route armed, so resolve the upstream with `rev-parse --symbolic-full-name @{u}` and surface an
unresolvable one as an explicit error state.

The same silence bounds deployment, since a checkout parked on a branch can only ever deploy that branch point rather
than main's tip and no verdict says so. Syncing the checkout out of that state is not always available, the branch often
being the operator's live work with uncommitted files. So move the ref rather than the tree. `git fetch origin
main:main` fast-forwards local `main` while the working tree stays on their branch untouched, which keeps the machine
current without ever putting their edits at risk.

### The local green proof is the only gate on main

Required status checks are configured on `main`, and the fleet's pushes do not satisfy them, they bypass them. The
remote answers each push reporting the rule violation as bypassed. Branch protection therefore never blocks a steward,
and a push that skipped its local validation would land unchallenged. The green-before-push proof each machine runs is
therefore the only thing actually protecting the branch, load-bearing rather than a second belt behind the ruleset.

Read the ruleset with `gh api repos/<owner>/<repo>/rules/branches/main` instead of inferring it from a push message.
Expect its required contexts to name JOBS while a run watcher reports WORKFLOWS. A watch on the workflow containing
those jobs is a superset of the ruleset and implies it, never the reverse. A context whose name matches a workflow name
exactly is a coincidence of that job being named after its workflow, not a counterexample.

Reading the push message instead invites a second wrong conclusion, since it reports every required check as expected
while none has reported yet, which is timing rather than a mismatch between contexts and jobs. The bypass is not the
whole gap either, because part of the check set is never invoked at all. A workflow triggered on `pull_request` alone
runs on no direct push. A fleet whose stewards never open one therefore publishes every commit without it, and coverage
sits in exactly that state.

A run watcher that catches every run a push produced is therefore complete for that push and still short of the
repository's full workflow set. Enumerate the workflow directory to see the difference rather than inferring it from a
run list.
