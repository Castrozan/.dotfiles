<resume_and_session_identity>
An agent's pinned session id is persisted to `~/clawde/session-ids/<agent>.json` before each launch and resumed on
every restart, not just on a redeploy nudge, so a crash no longer costs the conversation. A session that never wrote a
transcript is a phantom: `claude --resume` answers "No conversation found with session ID", and the wrapper forgets
that one id rather than wiping the whole record, so the fallback chain survives. When an agent keeps coming back
unresumed, suspect the workspace launcher crash-looping before it ever execs the harness, not the resume logic, because
a launcher that dies early never persists the id and every later read looks phantom.

The pinned id is a launch request, not an observation of what the harness opened. A `/clear`, a `/rewind` and a
compaction fork each mint a new session id inside the running process, and the wrapper never learns any of them, so
diagnose a session from the transcript directory rather than from the record. The transcript directory itself is
slugged from the harness process's cwd at launch, so an agent that execs from a subdirectory writes where nothing
looking at the configured workspace will find it.
</resume_and_session_identity>

<a_rebuilt_change_is_not_a_live_change>
Four layers apply at four different moments and the config on disk lies about all of them. Per-agent runtime config is
re-read on wrapper restart, so a warm redeploy applies it. Wrapper code keeps running whatever it launched with, so it
needs a full respawn. A `SKILL.md` edit is dormant on a resumed agent because the agent invokes its skill once at
session start and then runs hundreds of heartbeat ticks off that in-context copy; it lands on the next session
rotation, or immediately if you rotate deliberately. A model change deploys but does not reach a running session, and a
codex resume restores the model recorded in the session while ignoring `config.toml`, so force it by deleting the
session record and killing the process, which makes the next launch mint a fresh session that reads config.
</a_rebuilt_change_is_not_a_live_change>

<a_supervisor_restart_spares_everything_sharing_its_cgroup>
Restarting the supervisor unit reads like a fleet-wide outage and is not one. The unit sets `KillMode = process` and
declares no `ExecStop`, so systemd kills the supervisor pid alone and logs `Unit process N remains running after unit
stopped` for the multiplexer server, every wrapper, every harness under them and the human's own session, all of which
survive: one `herdr` pid was observed surviving two such stops four days apart. Read that journal line rather than any
warning before deciding a restart is too expensive. The unit's `X-RestartIfChanged = false` suppresses the churn and
guarantees nothing, three restarts having got through 105 home-manager activations in one measured week, so read the
fleet's live store paths rather than inferring them from the flag. What a restart does not do is refresh a
wrapper that survived it, so the rollout is still rebuild, restart, then kill the surviving wrappers for the supervisor
to recreate; darwin's launchd agent restarts on rebuild by itself. Compare wrapper store hashes before claiming a
rollout landed, because a green rebuild and a live fleet on new paths are separate facts.
</a_supervisor_restart_spares_everything_sharing_its_cgroup>

<supervisor_reconciles_by_wrapper_identity>
Reconciliation enumerates live `wrapper.py --agent-name X --config-file C` processes and matches on that, never on the
window name, terminating duplicates and orphans and creating a window only when no wrapper for the agent is running.
When an agent's window survives but its wrapper died, the supervisor relaunches into the existing window rather than
returning early, so use a respawn that replaces the pane and never a plain new-window; the restored-from-resurrect case
is exactly this, a real window holding a bare login shell.
</supervisor_reconciles_by_wrapper_identity>

<a_channel_bridge_is_a_headless_sidecar_not_a_window>
A harness carrying no in-process transport gets its channel driven by a bridge, and that bridge is a sidecar process the
supervisor owns directly, with no tab of its own, appending to `~/clawde/sidecar-logs/<name>.log` and found again
through the `pgrep` pattern its adapter declares. That pattern must not carry the bridge script's store path: edit the
script and the pattern matches nothing, so the previous generation's bridge is never culled and two clients hold one bot
token and answer everything twice. An eval check fails the build on a pattern containing a store path. The same matching
is why any shell command containing a reconcile pattern is terminated as a duplicate, so a `pgrep` typed to inspect a
bridge kills itself; assemble the pattern at runtime or run the inspection from a script file. The bridge takes no baked
one-shot command: it reads the agent's launch config, which carries one one-shot turn command per eligible harness, and
resolves the active harness from the runtime override on every message, so a manual `clawde harness <agent> <harness>`
or a failover rewires the Discord channel onto the new harness without the bridge restarting. Each turn is recorded in
the agent's harness-productivity record against that active harness, which is what lets a channel agent with no
heartbeat driver accrue the three-empty-turn refusal signature and fail over at all.
</a_channel_bridge_is_a_headless_sidecar_not_a_window>

<taking_an_agent_offline>
There is no per-agent `enable`. `onDemand = true` is the off switch: the supervisor never brings the agent up, so it
holds no process, no multiplexer window, no Discord connection and no firing heartbeat until someone runs `clawde start
<agent>`, which writes a lease file. Nothing asserts against pairing `onDemand` with a heartbeat interval, and the
heartbeat driver runs inside the agent's own window, so no window is what actually stops the schedule. Deleting an
agent that owned its own dedicated multiplexer session is worse: the supervisor only iterates sessions present in the
spec and has no pass that kills sessions absent from it, so the live session and its wrapper keep running forever and
must be killed by hand. Agents scheduled by a separate gateway keep their crons firing after being disabled, because
those live in a mutable store nix never writes. An on-demand agent that vanishes exactly one idle timeout after `clawde
start` did not crash: the lease went idle, the reconcile loop removed its window, and the give-away is the lease file
disappearing at `started_at` plus the timeout. The idle clock reads transcript modification times under the agent's
workspace, so a conversation the probe cannot see reads as no conversation at all.
</taking_an_agent_offline>

<launch_on_trigger_and_active_hours>
A `launchOnTrigger` agent runs one non-interactive turn per gate edge and exits, holding no process and no tab while
dormant; the tab appears when the gate fires and disappears when the cycle ends. The load-bearing rule is that exactly
one component may consume the edge fingerprint, since the gate fires only on change and a second reader swallows the
edge. Any agent opts into a token-cheap heartbeat the same way, by pointing `heartbeatGateCommand` at the change gate
with its own probe. The active-hours gate lives in the supervisor rather than the wrapper, so an out-of-hours agent is
fully stopped rather than idling, and it fails open. A one-shot turn cannot block on a long detached validation, which
is why an agent whose work outlives its own tick needs a warm headed session instead.
</launch_on_trigger_and_active_hours>

<multiplexer_backend>
An agent's session field is the multiplexer workspace label, not a session; there is one server session and workspaces
are the window-group analog. The backend is selected by an environment variable that the pane-run command does not
propagate into the pane, so the supervisor must inject it into the wrapper command explicitly or the heartbeat driver
silently falls back to the retired backend and crash-loops. Pane-state detection must key on the pane tail: the harness
renders inline with no alternate screen, so a wide capture catches stale scrollback and false-reads an idle prompt on a
pane that is actually wedged at a pre-prompt modal.
</multiplexer_backend>

<channel_gating>
A Discord agent that sends but receives nothing is almost always the plugin's own access gate, an empty per-agent
`access.json`, and almost never intents, gateway, plugin version or network: outbound is REST and needs no allowlist
while every inbound message is gated. Each host must use a distinct bot token, since the secrets decrypt everywhere and
two hosts running the same token both open a gateway connection and collide, with whichever process holds it answering.
Setting an explicit MCP config file is mutually exclusive with a plugin-provided channel, because the strict flag loads
only the named servers and excludes the plugin's own, which silently takes the bot offline.
</channel_gating>

<a_parked_agent_passes_every_liveness_probe>
An agent whose provider refuses work is indistinguishable from a healthy quiet one at every layer that watches it: the
wrapper process runs, the supervisor is satisfied, the heartbeat fires and is accepted, and the pane sits at its idle
prompt because a refused request returns in about two seconds. The pane check is worse than useless here, since it
short-circuits on the idle prompt before it ever looks for a quota banner, and opencode's banner scrolls away under the
next heartbeat anyway. Reading the pane cannot fix this either: `pane_is_at_idle_prompt` answers "the harness accepts
input", never "the harness is not working", and claude renders its input box permanently, so a healthy claude agent
scores an empty tick on every single send. The only honest signal is what the harness wrote, gathered on two channels
that cover different harnesses and combined so that missing evidence never counts against one. opencode and codex
report their own working state to herdr, which the driver samples across a window after each send, and that channel can
only ever vote a turn productive. claude reports nothing there but keeps a per-session transcript, so the driver counts
its entries just before it sends and compares at the next send: a refused request adds the delivered prompt and nothing
else, any real turn adds the prompt and at least one answer, so two is the line and no byte threshold has to be guessed.
Measuring after the send instead would miss every turn that finishes inside the window, which for a steward with nothing
to do is most of them. The run of empty ticks lands in `~/clawde/harness-productivity/<agent>.json`; three in a row is
the signature, and the supervisor and the health probe both read that one record. Failover reaches warm agents whose
turns land in a place clawde can count: heartbeat agents through the driver, and bridged channel agents through the
bridge recording each turn. A `launchOnTrigger` agent is the one class left out, because it runs one turn per gate edge
and holds no driver to observe.
</a_parked_agent_passes_every_liveness_probe>

<a_failover_is_a_loan_not_a_move>
The runtime moves a refused agent through `harnessFallbackChain` by writing the same override `clawde harness` writes,
so the two are one mechanism and the automatic one wins if it fires over a manual pin. It differs in carrying an expiry
and a `superseded_harness`, which is what sends the agent home a day later to retry the harness it was declared on, and
what makes `clawde harness <agent>` say it was moved rather than pinned. The rotation starts at the declared harness
and wraps, so a chain whose every entry is refusing keeps cycling instead of dead-ending on the last one. Nothing about
this reaches an agent with an empty chain: it stays parked, deliberately, and the health probe turns red instead.
</a_failover_is_a_loan_not_a_move>

<steward_loop>
A submodule divergence verdict is returned before every other verdict and short-circuits the whole loop, so the steward
keeps ticking and pushes nothing no matter how green CI is; the recoverable shape is now rebased automatically and only
a genuine gitlink-versus-gitlink conflict still needs a human. The steward defers when it reads recent commits as the
operator working, but peer agents commit under the same identity, so on a busy fleet the quiet window never arrives;
unblock it through its inbox rather than by loosening its caution. A growing unpushed chain is usually that same
learned caution ratcheted incident by incident, not a broken verdict. Its health probe is capped at sixty seconds and
reports the timeout exit as a parse error, which trains it off its own primary tool. Adding a single verdict is
shotgun surgery across five code sites plus four instruction tags, so budget for that before proposing one.
</steward_loop>

<self_activation_is_written_for_systemd_and_records_only_its_successes>
The activation helper refuses to launch on darwin before doing any work, because its entry point exits when
`systemd-run` is absent and its worker drives `systemctl --user`, so the self-activation step is dead on every darwin
machine and only the linux one can use it as shipped. Reach the same code through its detached-worker entry point under
a detach the platform actually has, a double `fork()` plus `os.setsid()` from a granted pane, which also keeps the
switch alive when the pane dies mid-activation; the refusal is the launcher being linux-shaped, never the machine being
ineligible. Two traps sit behind that gate and bite only once a steward really is the activator. Health is sampled
immediately after the switch with no settle delay and no retry, and any label that passed before and fails after counts
as a regression, so a service still coming up reads as one and arms the rollback, which is gated on the host being NixOS
and so is live on exactly one machine, the one where the operator rebuilds by hand within minutes of each commit, which
is why that rollback has never once executed. Whether the transition is rare is a question about which AGENT a probe
names, not about load, and the difference decides whether a machine is at risk. Measured across eight consecutive
validations on the linux machine, one agent's pane-responsiveness probe failed every single time in the post-build
health sample while its own liveness probe stayed green, and it passed in every standalone health-check between them.
That looks like load until the same sample is read whole: the two sibling agents' responsiveness probes pass in that
identical sample, at the same instant under the same build, so load is shared and cannot be what separates them. The
agent that fails is the odd one by class, a gate-launched one-shot running a non-interactive `exec` turn rather than a
warm interactive session like the two that pass, which is the difference to suspect first when only one probe of a kind
misbehaves. What survives is narrow and still serious: one agent on one machine
reliably presents the pass-then-fail pair, and that machine is the one where the rollback is armed. And the
last-activated record is written on the success path alone, so a
failed or rolled-back activation leaves it naming the previous revision: it is wrong in precisely the case you consult
it. Audit an activation by store path instead, comparing `/run/current-system` before and after against the closure the
validating build produced, and read the record as a claim rather than evidence. `/run/current-system` disagreeing with
`/nix/var/nix/profiles/system` means the switch aborted after the profile advanced. That audit carries an ordering
constraint worth holding, because losing it costs the evidence rather than the machine. Every host whose build resolves
the stewarded repo through a `git+file` reference has it, whether that reference is a wrapper flake taking the checkout
as an input or the checkout itself, which is the darwin backend's form: resolving the flake's toplevel answers for
whatever the checkout holds right now, so the one-command check exists only while the checkout still sits on the
revision in question and returns a different closure the moment you sync. On the direct form it is sharper still, since
a lockless `git+file` reads tracked working-tree content rather than HEAD, so an uncommitted edit moves the answer
without any sync at all. Capture the live closure's identity before moving the checkout, never after, or attributing a
generation somebody else activated needs an explicit input override to reproduce.
</self_activation_is_written_for_systemd_and_records_only_its_successes>

<a_post_switch_regression_costs_the_record_even_where_it_cannot_roll_back>
Off NixOS the rollback is not merely gated, it is skipped outright with a null exit code and a line saying automatic
rollback is unavailable, which reads like the trap being harmless there. It is not, because the regression branch
returns before the last-activated write is reached, so nothing is ever stamped. The outcome on such a host is that the
switch succeeds and stays live, the result records a regression, and the record still names the previous revision: a
successful activation filed as a failure. The two defects are one chain rather than two neighbours, since the health
trap is what triggers the ledger trap, and what it costs is exactly the evidence a later steward consults to decide what
is running. Audit by store path and the chain is visible; trust the record and it is invisible. Whether a given clean
activation is evidence at all turns on which probes were actually sampled. An agent-responsiveness probe whose
applicability gate is tied to that agent's active hours skips outside them, and a skipped probe presents no
pass-then-fail pair, so an after-hours run tells you nothing about a gated probe whatever the code does. It does not
follow that the host is untested, because gating is per agent rather than per host and one machine routinely carries
both kinds; an ungated probe sitting green on both sides of the switch is real evidence, and it is evidence from the
worst possible window. Enumerate the probes that ran before drawing either conclusion, and enumerate them from a full
probe listing rather than from a status summary, since a summary that reports failures and skips never reports what
quietly passed and reading one as an inventory is how a live ungated probe goes unnoticed. Measured across three
machines the load-deterministic failure appears on one agent's probe on one host and on no other, so treat it as a
property of the agent being probed until some second agent reproduces it, never as a property of the platform or the
hour.
</a_post_switch_regression_costs_the_record_even_where_it_cannot_roll_back>

<a_verdict_that_cannot_tell_reports_all_clear>
The steward's divergence count comes from asking git for a remote branch name built by concatenating `origin/` with the
branch it believes it is on, never by resolving the configured upstream, and both failure paths return zero behind and
zero ahead. A second route reaches the same place: the branch helper returns the literal string `unknown` when
`rev-parse` fails, and that interpolates into the same name, so a detached HEAD asks for `origin/unknown` and lands on
the identical zero. Either way "cannot determine" is published as "no divergence", which is worse than an error, because
a steward reading zero behind stops looking; it recurred four times on one machine before anyone caught it. Guarding the
concatenation alone leaves the second route armed, so resolve the upstream with `rev-parse --symbolic-full-name @{u}`
and surface an unresolvable one as an explicit error state. The same silence bounds deployment, since a checkout parked
on a branch can only ever deploy that branch point rather than main's tip and no verdict says so. Syncing the checkout
out of that state is not always available, the branch often being the operator's live work with uncommitted files, so
move the ref rather than the tree: `git fetch origin main:main` fast-forwards local `main` while the working tree stays
on their branch untouched, which keeps the machine current without ever putting their edits at risk.
</a_verdict_that_cannot_tell_reports_all_clear>

<the_local_green_proof_is_the_only_gate_on_main>
Required status checks are configured on `main`, and the fleet's pushes do not satisfy them, they bypass them: the
remote answers each push reporting the rule violation as bypassed, so branch protection never blocks a steward and a
push that skipped its local validation would land unchallenged. The green-before-push proof each machine runs is
therefore the only thing actually protecting the branch, load-bearing rather than a second belt behind the ruleset. Read
the ruleset with `gh api repos/<owner>/<repo>/rules/branches/main` instead of inferring it from a push message, and
expect its required contexts to name JOBS while a run watcher reports WORKFLOWS; a watch on the workflow containing
those jobs is a superset of the ruleset and implies it, never the reverse. A context whose name matches a workflow name
exactly is a coincidence of that job being named after its workflow, not a counterexample. Reading the push message
instead invites a second wrong conclusion, since it reports every required check as expected while none has reported
yet, which is timing rather than a mismatch between contexts and jobs. The bypass is not the whole gap either, because
part of the check set is never invoked at all: a workflow triggered on `pull_request` alone runs on no direct push, so a
fleet whose stewards never open one publishes every commit without it, and coverage sits in exactly that state. A run
watcher that catches every run a push produced is therefore complete for that push and still short of the repository's
full workflow set, so enumerate the workflow directory to see the difference rather than inferring it from a run list.
</the_local_green_proof_is_the_only_gate_on_main>

<a_worker_that_runs_in_the_tree_it_proves_can_void_its_own_proof>
A validation worker whose cwd is the checkout writes into the tree it is proving, and a redirect fires before the
command feeding it fails, so a broken command chain still leaves a file behind. The build then succeeds against a dirty
tree and the proof is worthless while still reading exit 0, so consume the dirty flag alongside the exit code and never
the code alone. The defence is ordering inside the runner and is two lines: open the worker log at an absolute path
under the state directory, chdir there, then invoke the build, after which even a careless relative redirect lands
outside the tree. What hides the litter is that a 0-byte file at the repo root is untracked, so a porcelain status
passing `--untracked-files=no` calls the tree clean; check untracked explicitly. Ordering protects cwd and not HEAD:
any phase resolving the flake from the checkout rather than a pinned rev reads HEAD at eval time, so a commit landing
mid-validation reproves a different revision than the result file is named after. Capture HEAD at worker start and
compare at the end, and hold commits while such a phase is in flight.
</a_worker_that_runs_in_the_tree_it_proves_can_void_its_own_proof>

<a_process_match_that_can_match_the_matcher>
Any pattern matched against process command lines must be written so it cannot match the command doing the matching,
because whether it does depends on how the harness wrapped that command rather than on intent, and the same pattern
self-matches in one invocation and not the next on one machine. The failure is silent in both directions: on the kill
side it terminates your own shell instead of the worker, and on the read side it counts your own shell as a live
worker, so a finished detached job reads as still running. Write the bracket form, `validate-runner[.]py`, which cannot
match itself and returns the identical result where the naive pattern was already fine. Reading the matched command
line rather than the pid count is what catches it after the fact.
</a_process_match_that_can_match_the_matcher>

<a_check_you_have_only_seen_pass_is_untested>
A verification whose success output does not depend on its measurement is not a verification: an unconditional ok line
prints beside the violation it was meant to catch, and a checker pointed at a mistyped path reports a silence that
reads as clean. Make the success branch conditional on finding zero violations, fail loudly on an unreadable target,
and prove the failure paths by forcing them once, tightening the threshold until it fires and aiming it at a
nonexistent file, before trusting the passing case.
</a_check_you_have_only_seen_pass_is_untested>

<which_tree_a_prose_edit_lands_in_decides_whether_it_owes_an_activation>
A commit touching only prose is not automatically activation-free, because part of the instruction tree is materialized
into the system closure and part is read from the checkout at runtime: the skills tree is symlinked in from
home-manager files and so ships in a closure, while the harness tree is reached by repo-relative path from an
instruction file that is itself in a closure, so its content is read live. Editing
`agent-harness/agent-instructions/skills/<skill>/knowledge.md` therefore owes a switch and editing
`agent-harness/harnesses/<harness>/knowledge.md` does not, confirmed on three machines across two platforms. Resolve
the wrapper toplevel and compare against the running system rather than assuming a docs commit changes nothing, and do
not use the toplevel the validation result records until you have checked that what it built is what deploys, which no
result file states: where a wrapper flake sits between repo and deploy that path is the revision-pinned bare build, a
different derivation that never equals the running system, so comparing the two answers a question about neither. A
host where the comparison is valid is usually safe by the shape of its backend rather than by anyone having checked,
which is why the check belongs in the reader and not in the host. Pin the revision into the deployed flake instead,
with `nix eval --override-input dotfiles <repo>?rev=<sha>` against the wrapper, which answers for any revision without
moving the checkout.
</which_tree_a_prose_edit_lands_in_decides_whether_it_owes_an_activation>

<pushing_to_a_stewarded_repo>
The steward shares the same checkout and continuously rebases and pushes `main`, so local `main` routinely diverges
mid-session and the submodule is often dirty during a sync. Land a single commit through a detached worktree
cherry-picked onto `origin/main` and fast-forward push it, rather than reconciling a diverged history by hand and
racing the loop.
</pushing_to_a_stewarded_repo>

<the_service_cgroup_is_the_whole_shared_server>
The service cgroup is not the agent fleet. It holds the shared multiplexer server, so everything that server hosts is
accounted to it: the fleet, the steward, the human's interactive session, and every command that session launches, a
rebuild included. Read `/proc/self/cgroup` from an interactive pane and it names the clawde unit. Any memory knob on
that unit therefore throttles the human, and a ceiling sized to the fleet's resting set starves the rebuild that would
deploy it. `MemoryHigh` alone relocates pages into swap rather than reducing them, so a ceiling under the honest
working set trades a RAM shortage for a swap exhaustion and leaves the desktop worse off. Size such a ceiling as a
runaway backstop above the resting set plus a concurrent build, never as a daily throttle, and never add
`MemorySwapMax` while swap is already full, which converts throttling into OOM kills.
</the_service_cgroup_is_the_whole_shared_server>

<a_quota_dead_agent_reads_as_healthy>
An agent whose model has exhausted its quota is the hardest fleet failure to see, because every layer reports fine: the
supervisor finds a live wrapper, the watchdog finds a pane parked at its idle prompt, the change gate keeps firing, and
each heartbeat submits cleanly and then dies inside the harness leaving an empty assistant turn. The only tell is a
banner in the pane's own status row, and opencode parks on one for days behind a retry countdown rather than failing
the turn. So before suspecting the supervisor, the resume chain or the heartbeat driver, read the agent's pane wide
enough to catch that row and check the model's quota; a stack of submitted heartbeats with no replies under them is the
signature, and a workspace whose HEARTBEAT and inbox stopped moving days ago confirms it. That row also wraps mid-word
at the widths agents really run at, splitting a marker like `esc interrupt` across four lines, so any indicator matched
against it must ignore whitespace or it misses a banner that is plainly on screen.
</a_quota_dead_agent_reads_as_healthy>

<ci_sandbox_lacks_pgrep>
The nix build sandbox provides no `pgrep` on either platform, so any test that shells out to it fails the flake check
on both runners. Stub it in the unit `conftest.py` as an autouse fixture exiting non-zero with no output, which is
pgrep's genuine no-match behavior, rather than skipping the tests or reaching for the real binary.
</ci_sandbox_lacks_pgrep>
