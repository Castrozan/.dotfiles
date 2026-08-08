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
The unit sets `X-RestartIfChanged = false`, and a check asserts it, on the belief that a restart kills the multiplexer
server in its cgroup and destroys every agent window. Both halves are wrong as deployed. The flag does not hold, since
the unit has been stopped and restarted by activation while it was set, so never assume a rebuild left the fleet on the
previous store paths. The restart is also cheap, because the unit sets `KillMode = process` and declares no `ExecStop`,
so systemd kills the supervisor alone and logs `Unit process N remains running after unit stopped` for the multiplexer
server, every wrapper, every harness under them and the human's own session, all of which survive. Read that journal
line rather than the assertion's comment before warning anyone off a restart. What a restart does not do is refresh a
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
bridge kills itself; assemble the pattern at runtime or run the inspection from a script file.
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
the signature, and the supervisor and the health probe both read that one record. Failover only reaches warm
heartbeat agents, because a `launchOnTrigger` agent runs one turn per gate edge and holds no driver to observe.
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
