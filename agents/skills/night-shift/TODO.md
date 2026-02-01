# Night Shift — TODO / Backlog

Items to implement or improve for the night shift skill.

## Tonight's Task Queue (2026-01-31)

### Priority 0 — Implementation (Lucas requested)
- [ ] **Claude Code control via tmux/exec** — Cleber should start, monitor, and control Claude Code CLI sessions. Research pipe mode (`claude -p`), tmux sessions, pty exec. Build a skill or integrate with existing coding-agent skill. Test and validate end-to-end.

### Priority 1 — Research
- [ ] X/Twitter: AI trading & crypto agents — how are agents trading? Platforms, DeFi, Polymarket bots
- [ ] X/Twitter: Health/wellness trading via AI — any agents doing this?
- [ ] TTS/STT research — better voice solutions than edge-tts + faster-whisper, real-time voice conversation
- [ ] Multi-agent / swarm patterns — how to run many agents, make them collaborate
- [ ] New skills & tools — aitmpl.com agents, GitHub trending, Claude Code new features

### Priority 2 — Assessment & Analysis
- [ ] Security assessment — SSH configs, Tailscale network, exposed ports, agenix secrets, firewall
- [ ] Efficiency audit — token usage patterns, better X/Twitter tools, browser-use alternatives

### Priority 3 — Design & Planning
- [ ] Google Meet integration — virtual presence (avatar → webcam pipe, screen recording, audio transcription)
- [ ] Agent communication protocol — better bridge between Cleber ↔ Romário, swarm coordination

### Priority 4 — Processing
- [ ] Obsidian ReadItLater vault — process unread items, extract knowledge
- [ ] Compile morning summary

---

## Nix-Managed openclaw.json (Configuration as Code)

Goal: manage as many `openclaw.json` fields as possible via Nix, using a Home Manager activation script with `jq` to patch the runtime config on each rebuild. The config stays at `~/.openclaw/openclaw.json` (OpenClaw owns it), but Nix ensures critical fields are always correct.

### Fields to Nix-Manage

| Field | Current Value | Nix Source |
|-------|--------------|------------|
| `agents.defaults.workspace` | `/home/zanoni/clawd` | Derive from home.homeDirectory |
| `channels.telegram.tokenFile` | `/run/agenix/telegram-bot-token` | agenix secret path |
| `tools.web.search.apiKey` | hardcoded in JSON | Read from `/run/agenix/brave-api-key` |
| `tools.media.audio.models[0].command` | `/home/zanoni/clawd/scripts/faster-whisper.sh` | Derive from scripts symlink path |
| `tools.media.audio.models[0].args` | Whisper model config | Define in Nix (model, format, output dir) |
| `tools.exec.pathPrepend` | Hardcoded Nix store paths | Derive from actual Nix profile paths |
| `gateway.port` | `18789` | Nix option |
| `gateway.bind` | `tailnet` | Nix option |
| `gateway.auth.token` | Hardcoded | Read from `/run/agenix/openclaw-gateway-token` |

### Implementation Approach

**Home Manager activation script** that runs on each rebuild:
```nix
# Pseudocode — actual implementation TBD
home.activation.patchOpenclawConfig = lib.hm.dag.entryAfter ["writeBoundary"] ''
  CONFIG="$HOME/.openclaw/openclaw.json"
  if [ -f "$CONFIG" ]; then
    ${pkgs.jq}/bin/jq '
      .agents.defaults.workspace = "/home/zanoni/clawd" |
      .channels.telegram.tokenFile = "/run/agenix/telegram-bot-token" |
      .tools.web.search.apiKey = (input | rtrimstr("\n")) |
      .tools.media.audio.models[0].command = "/home/zanoni/clawd/scripts/faster-whisper.sh" |
      .gateway.auth.token = (input | rtrimstr("\n"))
    ' "$CONFIG" \
      /run/agenix/brave-api-key \
      /run/agenix/openclaw-gateway-token \
    | ${pkgs.moreutils}/bin/sponge "$CONFIG"
  fi
'';
```

### Benefits
- **Secrets never in git** — API keys read from agenix at activation time
- **Paths always correct** — Nix store paths update automatically on rebuild
- **Single source of truth** — Nix defines what matters, OpenClaw owns the rest
- **Non-destructive** — jq patches only specific fields, preserves runtime changes

### Risks & Mitigations
- **OpenClaw wizard could overwrite** — activation runs after wizard; test ordering
- **Race condition** — gateway could be running during activation; may need restart after patch
- **Array mutations** — jq array updates are fragile; use `setpath` for nested arrays

### Steps to Implement
- [ ] Create `~/.dotfiles/home/modules/openclaw/activation.nix` with jq patch script
- [ ] Define Nix options for configurable fields (workspace, port, bind, whisper model)
- [ ] Read secrets from agenix paths in activation script
- [ ] Test: rebuild → verify openclaw.json has correct values
- [ ] Test: gateway restart picks up patched config
- [ ] Add to default.nix imports
- [ ] Remove hardcoded secrets from openclaw.json (gateway token, brave key)

---

## Research Findings (2026-01-31)

### Cursor: Scaling Long-Running Autonomous Coding
- **Source**: cursor.com/blog/scaling-agents
- Ran hundreds of agents for weeks, built a browser from scratch (1M LoC)
- Key insight: flat agent coordination fails — agents become risk-averse
- **Planner-Worker pattern works**: planners create tasks, workers grind, judge evaluates
- GPT-5.2 better than Opus 4.5 for extended autonomous work (fewer shortcuts)
- **Takeaway for us**: Our orchestrator→sub-agent design is validated. Consider planner sub-agent for complex nights.

### AGENTS.md Impact on AI Coding Agents (Academic Paper)
- **Source**: arxiv.org/html/2601.20404 (Jan 2026)
- AGENTS.md files reduce runtime by 29% and output tokens by 17%
- 60,000+ repos now use AGENTS.md format
- **Takeaway**: Our AGENTS.md is solid. Sub-agent spawns should include focused AGENTS.md-style instructions.

### OpenClaw Cron: Isolated agentTurn
- **Source**: docs.openclaw.ai/automation/cron-jobs
- Cron supports `sessionTarget: "isolated"` with `agentTurn` payload
- Each run gets fresh session (no context carry-over)
- Supports model/thinking overrides per job (Sonnet for cheap, Opus for complex)
- Auto-delivers to Telegram with `deliver: true`
- **Takeaway**: Use isolated cron jobs for research tasks (cheaper, focused). Main session only for orchestration.

### Token Burn Warning (GitHub Issue #1594)
- Even "no-op" cron runs consume tokens
- Never run big output tools in main session
- **Takeaway**: HEARTBEAT_OK is cheap but not free. Isolated cron jobs are better than heartbeat for scheduled work.

### Brave Search Rate Limit
- Free tier: 1 request/second, 2000 queries/month
- We hit 429 rate limit during parallel searches
- **Takeaway**: Add 1.5s delay between web_search calls, or upgrade plan

## Research Capability Improvements
- [x] **Configure Brave Search API key** — done, working
- [ ] **Use `jq`/`yq` for JSON state management** — surgical updates instead of full file rewrites
- [ ] **Build X/Twitter reader script** — `web_fetch` doesn't work on X (dynamic), need dedicated tool
- [ ] **Browser-use optimization** — light mode only, minimize tab count, close after use
- [ ] **Cache research results** — avoid re-fetching same URLs across sub-agents

## Research Capability Improvements (High Priority)

### Search & Discovery
- [ ] Activate twikit auth — need Twitter credentials to unlock X search (venv at `~/.local/share/twikit-venv/`)
- [ ] Brave Search rate limiting — implement 1req/sec throttle in research sub-agents
- [ ] Add Tavily as fallback search (1K free/month) when Brave is rate-limited
- [ ] Build `site:x.com` Brave Search wrapper for auth-free X content discovery
- [ ] Evaluate Jina Reader (`r.jina.ai/URL`) for extracting X thread content

### Architecture (from research)
- [ ] Implement judge agent — evaluates sub-agent output quality before accepting
- [ ] Narrow sub-agent scopes — each agent does ONE thing (search, synthesize, build, audit)
- [ ] Structured task queue (JSON) instead of simple rotation — priority, dependencies, retry
- [ ] Add cycle evaluation — after N tasks, assess what worked and adjust priorities
- [ ] Parallel worker spawning for independent research tasks

## Skill Improvements (Future)

### Sub-Agent Templates
- [ ] Create reusable prompt templates for common sub-agent tasks (research, build, security)
- [ ] Test sessions_spawn with different task types — what works, what doesn't
- [ ] Figure out sub-agent tool access — do spawned agents get browser? exec?

### Cron Optimization
- [ ] Tune cron interval based on average task duration (measure first night)
- [ ] Add adaptive spacing — if tasks complete fast, fire next sooner
- [ ] Consider parallel spawns for independent research tasks

### Browser Efficiency
- [ ] Investigate dedicated X/Twitter CLI tools (twikit, nitter scraping, API alternatives)
- [ ] Test `web_fetch` on x.com — does it work without browser?
- [ ] Build a lightweight X reader script if needed

### Output Quality
- [ ] Define output templates per task type (research, security, build)
- [ ] Add automatic cross-referencing between task outputs
- [ ] Morning summary should link to individual files

### Integration
- [ ] Connect findings to Obsidian vault (copy relevant files to vault)
- [ ] Auto-create Obsidian notes from research findings
- [ ] Tag system for discoveries (actionable vs reference vs idea)

## Design Decisions to Make

1. **Cron interval**: 20min seems right. Measure actual task durations first night and adjust.
2. **Browser strategy**: Use `web_search` + `web_fetch` first. Only launch browser for X/Twitter or authenticated sites.
3. **Sub-agent model**: Same as main (Opus) or cheaper (Sonnet) for routine research?
4. **Parallel vs sequential**: Start sequential, test parallel after first successful night.
5. **State persistence**: state.json is simple but fragile. Consider if we need something more robust.

## Known Issues

- `sessions_spawn` only has `main` agent configured — spawned agents inherit main's tools
- Browser-use with Brave full profile causes Playwright timeouts (too many tabs)
- X/Twitter is dynamic — `web_fetch` won't work, need browser or API
- Voice message transcription via gateway still being debugged (faster-whisper subprocess issue)
