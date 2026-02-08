# Night Shift — Autonomous Overnight Work

Continuous autonomous work mode. The agent works through the night, spawning parallel sub-agents and processing results as they complete.

## When to Use
User says: "night shift", "work through the night", "autonomous mode", "keep working while I sleep"

## Architecture

```
Heartbeat-driven continuous loop:

Main Session (Orchestrator/Opus):
  → Reads state.json, spawns 2-4 sub-agents IN PARALLEL
  → As sub-agents complete (announce messages), immediately:
     1. Update state.json
     2. Spawn replacement sub-agents for next tasks
     3. Repeat until queue empty
  → Cron is ONLY a safety net — restarts work if agent dies

Sub-Agents (Workers/Sonnet):
  → Focused single task, fresh context
  → Write output to project dir
  → Report back automatically via announce
```

### Why Parallel
Sequential sub-agents = 1 task per cycle = slow. **Always spawn 2-4 sub-agents at once.**
- Sub-agents are independent — no coordination needed between them
- Each takes 2-5 minutes; running 3 in parallel = 3x throughput
- sessions_spawn supports up to 4 concurrent, 8 max total
- Stagger slightly if they share resources (web_search rate limit)

### Safety Net Cron
One cron job ensures the agent keeps working even if it gets stuck or the session dies:
```
schedule: { kind: "every", everyMs: 1200000 }  # 20 min
payload: { kind: "systemEvent", text: "Night shift safety check: Read projects/night-shift-YYYY-MM-DD/state.json. If there are pending tasks and fewer than 2 sub-agents running, spawn more. If all done, compile summary." }
sessionTarget: "main"
```
This is NOT the main work driver — it's a fallback. The main loop is driven by sub-agent completions triggering the next wave.

### Execution Flow
```
1. Lucas says "activate night shift"
2. Create state.json with full task queue
3. Set safety cron (20 min)
4. Spawn 2-4 sub-agents immediately (first wave)
5. Sub-agent A completes → announce → spawn replacement
6. Sub-agent B completes → announce → spawn replacement
7. ... continuous pipeline until queue empty
8. Compile summary
9. Lucas wakes → remove cron, deliver report
```

### Model Strategy
- **Opus**: Orchestrator (main session), architecture/design, implementation decisions
- **Sonnet**: Research tasks, web scraping, file processing, routine work
- Set per-spawn with `model` parameter in `sessions_spawn`

### Sub-Agent Prompt Guidelines
Keep prompts **focused and minimal**:
- One clear objective per spawn
- List specific tools and search queries
- Specify exact output file path
- Do NOT include full workspace context — they inherit tools
- Add 2s delays between web_search calls (Brave rate limit: 1 req/sec)
- Use `label` parameter for tracking (e.g., `label: "vtuber-research-1"`)

### Delegation to Other Grid Agents
For tasks outside your role (work stuff → Robson), use bot-bridge:
```bash
~/openclaw/skills/agent-grid/scripts/bot-bridge.sh robson "Night shift task: [description]. Write output to ~/openclaw/projects/night-shift-YYYY-MM-DD/[filename].md"
```
Send all Robson tasks at the START of the night, not sequentially. He works in parallel too.

## Activation Sequence

### 1. Create Output Directory
```bash
mkdir -p projects/night-shift-YYYY-MM-DD/
```

### 2. Initialize State File
Write `projects/night-shift-YYYY-MM-DD/state.json`:
```json
{
  "date": "2026-01-31",
  "startedAt": "2026-01-31T22:00:00-03:00",
  "status": "active",
  "taskQueue": [
    {"id": "t01", "name": "Task Name", "status": "pending", "model": "sonnet"},
    {"id": "t02", "name": "Task Name", "status": "pending", "model": "sonnet"}
  ],
  "currentTask": null,
  "runningTasks": [],
  "completedTasks": [],
  "findings": []
}
```

### 3. Set Safety Cron
```
schedule: { kind: "every", everyMs: 1200000 }
sessionTarget: "main"
payload: { kind: "systemEvent", text: "Night shift safety check..." }
```

### 4. Spawn First Wave (2-4 sub-agents)
Immediately spawn multiple sub-agents. Don't wait for the first cron tick.
```
sessions_spawn(task="...", model="sonnet", label="task-name-1")
sessions_spawn(task="...", model="sonnet", label="task-name-2")
sessions_spawn(task="...", model="sonnet", label="task-name-3")
```

### 5. On Each Sub-Agent Completion
When an announce message arrives:
1. Update state.json (mark completed, add findings)
2. If pending tasks remain → spawn next sub-agent immediately
3. If all done → compile summary, notify if urgent
4. Track `runningTasks` array to avoid over-spawning (max 3-4 concurrent)

### 6. On Safety Cron Tick
- Check state.json
- If `runningTasks` < 2 and pending tasks exist → spawn more
- If all tasks done → compile summary and remove cron
- If nothing to do → HEARTBEAT_OK

## Task Types

### Research Tasks
Model: **Sonnet** (cheap, sufficient).
Tools: `web_search` → `web_fetch` → Jina Reader (`r.jina.ai/URL`) → `browser` (last resort).
Output: markdown file with TL;DR, Key Findings, Action Items, Sources.

### Build Tasks
Model: **Opus** for architecture, **Sonnet** for implementation.
Rules: branch (`night-shift/YYYY-MM-DD-topic`), never push to main.

### Processing Tasks
Obsidian vault, ReadItLater items, email digests.
Output: digest file + action items.

### Analysis Tasks
Review previous outputs, synthesize patterns, identify opportunities.
Run after research rounds to decide next steps.

## Output Structure

```
projects/night-shift-YYYY-MM-DD/
├── 00-plan.md                    # Task list and goals
├── 01-[task-name].md             # Individual task outputs
├── 02-[task-name].md
├── ...
├── summary.md                    # Morning summary
└── state.json                    # Night shift state
```

## Default Research Topics

Customize per night, but defaults:
1. **Efficiency** — Token optimization, faster workflows, better tools
2. **New Skills & Tools** — GitHub trending, new AI tools, CLI utilities
3. **Multi-Agent / Swarms** — Agent orchestration, communication patterns
4. **Virtual Presence** — Avatars, Meet bots, screen recording pipelines
5. **AI Agent Trading & Crypto** — Trading bots, DeFi, Polymarket
6. **Security Assessment** — SSH, Tailscale, firewall, secrets
7. **Obsidian Vault / ReadItLater** — Process saved items, organize knowledge

## Rules

### Must Follow
- **Drop everything if Lucas messages** — respond immediately
- **Parallel by default** — always 2-4 sub-agents running
- **One file per task** — never dump everything into one file
- **Track running tasks** — update state.json on every spawn/completion
- **Follow workspace structure** — output in `projects/`, not `memory/`

### Should Follow
- Rotate categories — mix research, build, and processing tasks
- Front-load Robson delegation — send ALL his tasks at night start
- If a task fails twice, mark it and move on
- Prefer `web_search` + `web_fetch` over browser (faster, cheaper)
- Use browser for dynamic sites (X/Twitter, authenticated pages)
- Label all sub-agents for tracking (`sessions_spawn` label param)

## Morning Summary

When user wakes up, compile `summary.md`:

```markdown
# 🌅 Night Shift Report — [Date]

## Highlights
- [Top 3-5 discoveries, one line each]

## Tasks Completed
| # | Task | Status | Output |
|---|------|--------|--------|

## Key Findings
- [Finding]: [Why it matters]

## Action Items
- [ ] [Next steps based on findings]

## Built Tonight
- [What was implemented, branch name]

## Process Notes
- Tasks completed: X/Y
- Parallelization: avg N concurrent sub-agents
- Improvements for next time: [lessons]
```

## Deactivation

Night shift ends when user says to stop. On deactivation:
1. Compile summary.md
2. Remove safety cron
3. Update state.json status to "completed"
4. Send morning summary
5. Reset HEARTBEAT.md
