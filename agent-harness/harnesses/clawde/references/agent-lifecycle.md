### Resume and session identity

An agent's pinned session id is persisted to `~/clawde/session-ids/<agent>.json` before each launch and resumed on every
restart, not just on a redeploy nudge, so a crash no longer costs the conversation. A session that never wrote a
transcript is a phantom: `claude --resume` answers "No conversation found with session ID", and the wrapper forgets that
one id rather than wiping the whole record, so the fallback chain survives. When an agent keeps coming back unresumed,
suspect the workspace launcher crash-looping before it ever execs the harness, not the resume logic, because a launcher
that dies early never persists the id and every later read looks phantom.

The pinned id is a launch request, not an observation of what the harness opened. A `/clear`, a `/rewind` and a
compaction fork each mint a new session id inside the running process, and the wrapper never learns any of them, so
diagnose a session from the transcript directory rather than from the record. The transcript directory itself is slugged
from the harness process's cwd at launch, so an agent that execs from a subdirectory writes where nothing looking at the
configured workspace will find it.

### A rebuilt change is not a live change

Four layers apply at four different moments and the config on disk lies about all of them. Per-agent runtime config is
re-read on wrapper restart, so a warm redeploy applies it. That warm redeploy is the rebuild entrypoint's own
post-switch `clawde-redeploy` nudge, not a clawde activation, so it reaches every platform the rebuild script runs on.

Wrapper code keeps running whatever it launched with, so it needs a full respawn. A `SKILL.md` edit is dormant on a
resumed agent because the agent invokes its skill once at session start and then runs hundreds of heartbeat ticks off
that in-context copy; it lands on the next session rotation, or immediately if you rotate deliberately.

A model change deploys but does not reach a running session, and a codex resume restores the model recorded in the
session while ignoring `config.toml`, so force it by deleting the session record and killing the process, which makes
the next launch mint a fresh session that reads config.

Codex channel resumes also retain their original `developer_instructions`; supplying new text with `-c` does not update
them. A fresh channel session is required for personality changes. The channel's resumable marker is separate from the
agent window's session record, so rotating the window alone does not refresh Discord.

### A supervisor restart spares everything sharing its cgroup

Restarting the supervisor unit reads like a fleet-wide outage and is not one. The unit sets `KillMode = process` and
declares no `ExecStop`, so systemd kills the supervisor pid alone and logs
`Unit process N remains running after unit stopped` for the multiplexer server, every wrapper, every harness under them
and the human's own session, all of which survive: one `herdr` pid was observed surviving two such stops four days
apart. Read that journal line rather than any warning before deciding a restart is too expensive.

The unit's `X-RestartIfChanged = false` suppresses the churn and guarantees nothing, three restarts having got through
105 home-manager activations in one measured week, so read the fleet's live store paths rather than inferring them from
the flag.

What a restart does not do is refresh a wrapper that survived it, so the rollout is still rebuild, restart, then kill
the surviving wrappers for the supervisor to recreate; darwin's launchd agent restarts on rebuild by itself. Compare
wrapper store hashes before claiming a rollout landed, because a green rebuild and a live fleet on new paths are
separate facts.

### Supervisor reconciles by wrapper identity

Reconciliation enumerates live `wrapper.py --agent-name X --config-file C` processes and matches on that, never on the
window name, terminating duplicates and orphans and creating a window only when no wrapper for the agent is running.
When an agent's window survives but its wrapper died, the supervisor relaunches into the existing window rather than
returning early, so use a respawn that replaces the pane and never a plain new-window; the restored-from-resurrect case
is exactly this, a real window holding a bare login shell.

On herdr that replacement has to create the new tab before it closes the stale one, because herdr refuses to close a
workspace's last tab, and a workspace holding one permanent agent beside on-demand ones sits at exactly one tab most of
the time. Get the order wrong and the close is refused, the create is never reached, and the agent stays dead through
every ten-second poll while its orphaned harness keeps sitting at an idle prompt, which is why the pane looks alive.

A relaunch blocked this way is recorded nowhere the agent can see it: the reason goes to the supervisor's stderr, at
`~/Library/Logs/clawde.err.log` on darwin and `journalctl --user -u clawde` on NixOS, so read that before concluding an
agent died of anything subtler.

### A channel bridge is a headless sidecar not a window

A harness carrying no in-process transport gets its channel driven by a bridge, and that bridge is a sidecar process the
supervisor owns directly, with no tab of its own, appending to `~/clawde/sidecar-logs/<name>.log` and found again
through the `pgrep` pattern its adapter declares.

That pattern must not carry the bridge script's store path: edit the script and the pattern matches nothing, so the
previous generation's bridge is never culled and two clients hold one bot token and answer everything twice. An eval
check fails the build on a pattern containing a store path.

The same matching is why any shell command containing a reconcile pattern is terminated as a duplicate, so a `pgrep`
typed to inspect a bridge kills itself; assemble the pattern at runtime or run the inspection from a script file.

### Channel bridge reconciliation

Because the pattern says nothing about which generation a live bridge came from, the supervisor records the command it
launched beside the log at `~/clawde/sidecar-logs/<name>.log.spawned-command` and replaces any live process whose record
no longer matches the command the current generation wants, terminating and waiting for each before spawning the
replacement. New bridge code therefore goes live within one supervisor poll of the rebuild that ships it, with no
respawn and no reboot; a bridge carrying no record at all counts as superseded and is replaced once.

The supervisor itself needed the same treatment for the same reason: its unit carries `X-RestartIfChanged = false`, so
home-manager rewrites the unit file and leaves the running process alone, and on chise that left the supervisor
executing a garbage-collected store path for three days while every rebuild reported success. A home activation now
compares the running supervisor's command line against the one the generation deploys and restarts only on a mismatch,
so a supervisor already on the current code is still never disturbed.

The bridge takes no baked one-shot command: it reads the agent's launch config, which carries one one-shot turn command
per eligible harness, and resolves the active harness from the runtime override on every message, so a manual
`clawde harness <agent> <harness>` or a failover rewires the Discord channel onto the new harness without the bridge
restarting. Each turn is recorded in the agent's harness-productivity record against that active harness, which is what
lets a channel agent with no heartbeat driver accrue the three-empty-turn refusal signature and fail over at all.

### Taking an agent offline

The per-agent `enable` is this repo's wiring, not upstream: `agent-enable.nix` filters `enable = false` agents out of
`config.clawde.agents` before the clawde module reads it, so the declaration stays in the tree while the supervisor
spawns no window, no Discord sidecar and no heartbeat for it, and any module that looks the agent up by name fails
evaluation.

`onDemand = true` is the softer switch: the supervisor never brings the agent up on its own, so it holds no process, no
multiplexer window and no firing heartbeat until someone runs `clawde start <agent>`, which writes a lease file, but a
`sidecarLifetime = "service"` bridge stays connected the whole time and keeps answering Discord through its own headless
turns. Nothing asserts against pairing `onDemand` with a heartbeat interval, and the heartbeat driver runs inside the
agent's own window, so no window is what actually stops the schedule.

Deleting an agent that owned its own dedicated multiplexer session is worse: the supervisor only iterates sessions
present in the spec and has no pass that kills sessions absent from it, so the live session and its wrapper keep running
forever and must be killed by hand. Agents scheduled by a separate gateway keep their crons firing after being disabled,
because those live in a mutable store nix never writes.

An on-demand agent that vanishes exactly one idle timeout after `clawde start` did not crash: the lease went idle, the
reconcile loop removed its window, and the give-away is the lease file disappearing at `started_at` plus the timeout.
The idle clock reads transcript modification times under the agent's workspace, so a conversation the probe cannot see
reads as no conversation at all.

### Launch on trigger and active hours

A `launchOnTrigger` agent runs one non-interactive turn per gate edge and exits, holding no process and no tab while
dormant; the tab appears when the gate fires and disappears when the cycle ends. The load-bearing rule is that exactly
one component may consume the edge fingerprint, since the gate fires only on change and a second reader swallows the
edge.

Any agent opts into a token-cheap heartbeat the same way, by pointing `heartbeatGateCommand` at the change gate with its
own probe. What that probe prints decides whether the gate is cheap at all: fold in a field the agent does not act on,
or one that peers move, and ordinary fleet traffic manufactures an edge every tick, so an edge-triggered gate silently
degrades into the level-triggered one it replaced. The steward's probe read the shared checkout's dirty flag, both
revision shas and the raw CI state, which cycles through its pending values on every push, and woke 73 times on one day
for a repository whose actionable state had barely moved.

Print the decision, not the state it was read from: a count of commits behind rather than the shas, a failing-or-not
boolean rather than the run's phase.

The active-hours gate lives in the supervisor rather than the wrapper, so an out-of-hours agent is fully stopped rather
than idling, and it fails open. A one-shot turn cannot block on a long detached validation, which is why an agent whose
work outlives its own tick needs a warm headed session instead.

### Multiplexer backend

An agent's session field is the multiplexer workspace label, not a session; there is one server session and workspaces
are the window-group analog. The backend is selected by an environment variable that the pane-run command does not
propagate into the pane, so the supervisor must inject it into the wrapper command explicitly or the heartbeat driver
silently falls back to the retired backend and crash-loops. Pane-state detection must key on the pane tail: the harness
renders inline with no alternate screen, so a wide capture catches stale scrollback and false-reads an idle prompt on a
pane that is actually wedged at a pre-prompt modal.

### Channel gating

A Discord agent that sends but receives nothing is almost always the plugin's own access gate, an empty per-agent
`access.json`, and almost never intents, gateway, plugin version or network: outbound is REST and needs no allowlist
while every inbound message is gated. Each host must use a distinct bot token, since the secrets decrypt everywhere and
two hosts running the same token both open a gateway connection and collide, with whichever process holds it answering.
Setting an explicit MCP config file is mutually exclusive with a plugin-provided channel, because the strict flag loads
only the named servers and excludes the plugin's own, which silently takes the bot offline.

### A parked agent passes every liveness probe

An agent whose provider refuses work is indistinguishable from a healthy quiet one at every layer that watches it: the
wrapper process runs, the supervisor is satisfied, the heartbeat fires and is accepted, and the pane sits at its idle
prompt because a refused request returns in about two seconds. The pane check is worse than useless here, since it
short-circuits on the idle prompt before it ever looks for a quota banner, and opencode's banner scrolls away under the
next heartbeat anyway.

Reading the pane cannot fix this either: `pane_is_at_idle_prompt` answers "the harness accepts input", never "the
harness is not working", and claude renders its input box permanently, so a healthy claude agent scores an empty tick on
every single send.

The only honest signal is what the harness wrote, gathered on two channels that cover different harnesses and combined
so that missing evidence never counts against one. opencode and codex report their own working state to herdr, which the
driver samples across a window after each send, and that channel can only ever vote a turn productive.

claude reports nothing there but keeps a per-session transcript, so the driver counts its entries just before it sends
and compares at the next send: a refused request adds the delivered prompt and nothing else, any real turn adds the
prompt and at least one answer, so two is the line and no byte threshold has to be guessed. Measuring after the send
instead would miss every turn that finishes inside the window, which for a steward with nothing to do is most of them.

The run of empty ticks lands in `~/clawde/harness-productivity/<agent>.json`; three in a row is the signature, and the
supervisor and the health probe both read that one record. Failover reaches warm agents whose turns land in a place
clawde can count: heartbeat agents through the driver, and bridged channel agents through the bridge recording each
turn. A `launchOnTrigger` agent is the one class left out, because it runs one turn per gate edge and holds no driver to
observe.

### A failover is a loan not a move

The runtime moves a refused agent through `harnessFallbackChain` by writing the same override `clawde harness` writes,
so the two are one mechanism and the automatic one wins if it fires over a manual pin. It differs in carrying an expiry
and a `superseded_harness`, which is what sends the agent home a day later to retry the harness it was declared on, and
what makes `clawde harness <agent>` say it was moved rather than pinned. The rotation starts at the declared harness and
wraps, so a chain whose every entry is refusing keeps cycling instead of dead-ending on the last one. Nothing about this
reaches an agent with an empty chain: it stays parked, deliberately, and the health probe turns red instead.
