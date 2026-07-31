---
name: clawde
description: Operate the clawde autonomous agent fleet - declare or change an agent, make a change actually reach the running agents, and debug one that is dead, unresumed, wedged, silent, or spending on the wrong model. Covers the steward loop. Read before touching any agent, supervisor, or heartbeat behavior.
---

<orientation>
clawde core is a standalone public flake at `github.com/Castrozan/clawde`, pinned as a dotfiles flake input and imported
as a home-manager module; nothing of it lives under `home/base/claude/` any more. Three parallel registries carry all
behavior and share one ABI: `clawde.channelAdapters` is how an agent talks, `clawde.agentTypes` is the role it plays,
and `clawde.harnesses` is what it runs. An agent picks one of each under `clawde.agents.<name>`; the public axes live in
the flake and the per-agent declarations live in private-config. A change to the flake reaches a machine only after it
is tagged there and the pin is bumped with `nix flake update clawde`, so an untagged commit is invisible no matter how
green it is.
</orientation>

<applying_a_change>
What a rebuild applies depends on which layer changed, and reading the config on disk lies about what the fleet is
actually running. Per-agent runtime config (heartbeat gate and interval, prompt, launch command, active hours,
rotation) is re-read by the wrapper on every restart, so a rebuild's warm redeploy applies it in place. Wrapper code is
not: the running wrapper keeps executing the code it launched with, so wrapper changes stay dormant until the window is
fully respawned. A model change reaches disk but not the live session. A rebuilt `SKILL.md` stays dormant on a resumed
agent until the session rotates. Always confirm against the live process rather than the config file, and see
`knowledge.md` for the platform asymmetry, which is the part that most often produces a false "rollout landed".
</applying_a_change>

<debugging_an_agent>
Work outward from the live process, never from the spec. `pgrep -f "wrapper.py --agent-name <name> --config-file"` is
the identity check the supervisor itself uses, and the `--config-file` delimiter is what stops the pattern matching a
prefix of a longer agent name. Compare the wrapper's store hash against the current generation before believing a
rollout. Read the agent's pane tail rather than a wide capture. Most symptoms that look like a clawde bug are one of
the known shapes in `knowledge.md`, so check there before opening an investigation.
</debugging_an_agent>

<talking_to_another_agent>
The `a2a` command is how one agent reaches another: `a2a list` shows every declared peer and whether it answers, `a2a
send <agent> <text>` drops a task and returns its id, and `a2a ask <agent> <text>` blocks until that agent finishes and
prints what it said. It reads `~/.claude/a2a/peers.json`, which a rebuild generates from the agents that set
`expose.a2a.enable`, so an agent missing from `a2a list` is undeclared rather than broken. There is deliberately no MCP
for this: the command costs nothing until you run it, while an MCP would put its tool schemas in every session prefix.
</talking_to_another_agent>

<knowledge>
`knowledge.md` holds the traps that cost real debugging and leave no trace in the source: resume and session identity,
the rebuild-versus-respawn matrix and its platform split, supervisor reconciliation, the multiplexer backend, channel
gating, and the steward loop. Read it before concluding that a clawde behavior is a defect rather than a known shape.
</knowledge>
