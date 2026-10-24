# Claude Code

Home-manager module that installs Claude Code and declares its configuration. `default.nix` composes the capability
modules; each subdirectory owns one capability.

## Distribution

The Claude binary is a prebuilt release pinned by version and per-platform hash in `launch/`. `claude-update-version`
moves the pin to the npm `latest` release, or to the version given as its argument, and prefetches the hash for every
supported platform.

## Ownership boundaries

- Shared MCP servers travel in the production plugin's `mcp-servers.nix`; `mcps/` adds only agent-only Claude servers
  and the selector clawde agents use to pick their servers.
- Hooks come from `agent-harness/hooks/`. The Claude integration deploys the shared runtime flat under
  `~/.claude/hooks/` and renders event registrations from the shared event-to-dispatcher map. Its walker deploys `.md`
  files too, so only a resource consumed by hook code or its interactive launcher belongs beside a hook. Before
  authoring a hook, read `docs/hook-output-channels.md` for which output reaches the model and which reaches only the
  human.
- Skills come from the shared interactive skill catalog, which owns the curated list for every harness;
  `docs/session-context-loading.md` explains the tiers. `private.nix` deploys private subagents and regular per-machine
  files, never directories, so a private skill reaches a session only through the catalog.
- `a2a` is provider-agnostic and lives in `agent-harness/agent-to-agent-communication/`; `claude-a2a-peer` launches its
  server for an existing herdr-attached agent.
- Persistent agents run under clawde through the harness-agnostic module in `agent-harness/harnesses/clawde/`; read its
  `knowledge.md` before changing agent, supervisor, or heartbeat behavior.

## Docs and tests

`docs/` holds module documentation that is not deployed. Module tests live in `__tests__/`; run the specific test file
or Nix check that covers the change.
