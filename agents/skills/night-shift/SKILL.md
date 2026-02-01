# Night Shift — Autonomous Overnight Work

Orchestrator-driven autonomous work mode. @agentName@ manages a task pipeline, delegating work to sub-agents and compiling results for morning review.

## When to Use
User says: "night shift", "work through the night", "autonomous mode", "keep working while I sleep"

## Architecture

```
Two cron strategies (mix and match):

A) Orchestrator pattern (main session):
   Cron (every 20min) → systemEvent → Main Session (Orchestrator)
     → Read state file, pick next task
     → sessions_spawn sub-agent with focused instructions
     → Sub-agent works, writes output file, reports back
     → Orchestrator decides: spawn another? write to memory? done?
     → Back to idle (zero cost until next cron)

B) Direct isolated cron jobs (no orchestrator needed):
   Cron → agentTurn (isolated session, can use Sonnet for cheap research)
     → Fresh session, focused prompt, auto-delivers results
     → Posts summary to main session
     → Optional: deliver to Telegram directly
```

### Cron Execution Modes
- **Main session (systemEvent)**: Orchestrator pattern. Good for coordination.
  - Uses `sessionTarget: "main"`, `payload.kind: "systemEvent"`
  - Agent wakes in main session with full context
- **Isolated session (agentTurn)**: Independent worker. Good for focused tasks.
  - Uses `sessionTarget: "isolated"`, `payload.kind: "agentTurn"`
  - Fresh session each run (no context bloat)
  - Supports `model` override (use Sonnet for research, Opus for complex work)
  - Supports `deliver: true` to send output directly to Telegram
  - Auto-posts summary to main session

### Why Sub-Agents
- Main session stays lean (no bloated context)
- Each task gets fresh context window
- Parallel work possible (spawn multiple, 4 max via sessions_spawn, 8 max concurrent)
- Failures are isolated — one bad task doesn't kill the night
- **Token efficiency**: sub-agents with trimmed context use ~17% fewer tokens (proven by research)

### Model Strategy (Cost Optimization)
- **Opus**: Orchestrator (main session), complex analysis, implementation decisions
- **Sonnet**: Research tasks, web scraping, file processing, routine work
- Set per-job with `model` override in cron or `sessions_spawn`
- Cursor found different models excel at different roles — match model to task

### Orchestrator Role — Planner-Worker Pattern
Based on Cursor's battle-tested findings (hundreds of agents, weeks of autonomous work):
- **Planner** (main session/Opus): Reads state, creates focused tasks, assigns to workers
- **Workers** (sub-agents/Sonnet): Grind on assigned task, zero inter-worker coordination
- **No QA bottleneck**: Workers report directly back, planner synthesizes
- **Prompts > architecture**: Well-crafted sub-agent prompts matter more than complex coordination
- Filesystem IS the shared state — task files + output files in `memory/night-shift/`

Orchestrator responsibilities:
- Reads task rotation from state file
- Crafts specific, focused prompts for each sub-agent (minimal context, clear objective)
- Spawns sub-agents with necessary tools and constraints available on the workspace
- Reviews sub-agent output when they report back
- Decides follow-up actions (more research? implementation? just save?)
- Compiles morning summary at the end

### Sub-Agent Prompt Guidelines
Keep sub-agent prompts **focused and minimal** to reduce token usage:
- One clear objective per spawn
- List specific tools to use
- Specify exact output file path and format
- Include search queries when relevant (saves the agent planning time)
- Do NOT include full workspace context (TOOLS.md, etc.) — they inherit tools automatically
- Add 2s delays between web_search calls (Brave rate limit: 1 req/sec)

## Activation Sequence

### 1. Create Output Directory
```bash
mkdir -p memory/night-shift/YYYY-MM-DD/
```

### 2. Initialize State File
Write `memory/night-shift/state.json`:
```json
{
  "date": "2026-01-31",
  "startedAt": "2026-01-31T22:00:00-03:00",
  "status": "active",
  "taskQueue": [
    {"id": "task-1", "name": "X/Twitter Research", "status": "pending"},
    {"id": "task-2", "name": "Security Assessment", "status": "pending"}
  ],
  "currentTask": null,
  "completedTasks": [],
  "findings": []
}
```

### 3. Set Up Cron
One cron job — systemEvent to main session, every 20 minutes:
If previous task still running, do them both by spawning another sub-agent.
```
schedule: { kind: "every", everyMs: 1200000 }
payload: { kind: "systemEvent", text: "Night shift: execute next task from the rotation. Read memory/night-shift/state.json, pick the next pending task, spawn a sub-agent for it." }
sessionTarget: "main"
```

### 4. Define Task Queue
The task queue lives in state.json. Each task has:
- `id`: unique identifier
- `name`: human-readable name
- `status`: pending | running | completed | failed
- `outputFile`: path to output (set when completed)
- `subAgentSession`: session key (set when spawned)

## Task Types

### Research Tasks
Sub-agent gets: topic, search strategy, output format.
Tools (priority order): `web_search` (Brave), `web_fetch`, Jina Reader (`r.jina.ai/URL`), `browser` (last resort).
Model: **Sonnet** (cheap, sufficient for research).
Output: markdown file with structured findings.

```
Sub-agent prompt template:
"Research [TOPIC]. Use web_search with queries: [Q1], [Q2], [Q3].
Fetch top 3-5 results. Write structured report to [OUTPUT_FILE].
Format: TL;DR, Key Findings (bullets), Notable Projects/Tools,
Action Items, Sources. Be thorough but concise."
Instruction files: Follow these guidelines [RULE_FILE_X], [RULE_FILE_Y], [CONDUCT_GUIDELINES_Z], [CONSTRAINTS]
```

### Build Tasks
Sub-agent gets: what to build, constraints, branch name.
Rules: always create branch (`night-shift/YYYY-MM-DD-topic`), never push to main, follow the instructions of [RULE_FILE_X], [RULE_FILE_Y], [CONDUCT_GUIDELINES_Z], [CONSTRAINTS].

### Processing Tasks (ReadItLater, Vault)
Sub-agent gets: Descriptive task based on the note to process. Why the note matters, how to extract value.
Output: digest file + processed item tags. Suggestion for next steps if relevant.

### Analysis Tasks
Sub-agent reviews previous task outputs, synthesizes patterns, identifies opportunities.
Used after research rounds to decide what to build or investigate further.

## Output Structure

```
memory/night-shift/YYYY-MM-DD/
├── 00-plan.md                    # Task list and goals for the night
├── 01-[task-name].md             # Individual task outputs
├── 02-[task-name].md
├── ...
├── summary.md                    # Compiled morning summary
└── state.json                    # Symlink to active state (optional)
```

Each output file is self-contained — readable on its own without context.

### File Naming
- Prefix with zero-padded number for ordering: `01-`, `02-`, etc.
- Kebab-case task name: `03-tts-stt-research.md`
- Summary is always last: `summary.md`

## Default Research Topics

Customize per night, but defaults:

1. **Obsidian Vault / ReadItLater** — Process saved items, extract knowledge, organize.
2. **Efficiency** — Better ways to browse X, read pages, reduce token usage, faster workflows.
3. **TTS/STT Solutions** — Best voice interaction for AI agents. Edge-TTS alternatives, Whisper improvements, real-time voice.
3. **New Skills & Tools** — GitHub trending, aitmpl.com, new Claude Code capabilities, useful CLI tools.
4. **Multi-Agent / Swarms** — How to orchestrate many agents. Claude Code swarms, OpenClaw multi-instance, agent communication.
5. **Virtual Presence** — Google Meet bots, webcam avatars, screen recording + transcription pipelines.
6. **AI Agent Trading & Crypto** — How agents trade on exchanges, DeFi, Polymarket. Tools, frameworks, risks.
7. **Security Assessment** — SSH, Tailscale, exposed ports, firewall, secrets management. Our two machines.

## Rules

### Must Follow
- **Drop everything if @userName@ messages** — respond immediately, night shift can wait
- **One file per task** — never dump everything into one giant file
- **Worktrees and branches only** — code changes go to `night-shift/` worktree branches, never main directly (things can go on main if tested and very relevant)

### Should Follow
- Rotate task categories — don't do 3 research tasks in a row if a build is ready
- Keep sub-agent prompts focused — one clear objective per spawn - multiple spawns if needed until task is done
- Log progress to state.json after each task
- If a task fails many times, mark it and move on
- Prefer `web_search` + `web_fetch` over browser when possible (faster, cheaper)
- Use browser only for dynamic sites (X/Twitter, authenticated pages)
- Use the user profile so to have access to saved passwords, cookies, etc. (you have permission and sub-agents as well)

## Morning Summary

When User wakes up or tells you to stop, compile `summary.md`:

```markdown
# 🌅 Night Shift Report — [Date]

## Highlights
- [Most important 3-5 discoveries, one line each]

## Tasks Completed
| # | Task | Status | Output |
|---|------|--------|--------|
| 1 | X/Trading Research | ✅ | 01-x-trading.md |
| 2 | Security Assessment | ✅ | 02-security.md |
...

## Key Findings
### [Category]
- [Finding]: [Why it matters]

## Action Items
- [ ] [Thing to do based on findings]

## Built Tonight
- [What was implemented, branch name]

## System Health
- Services: [status]
- Disk: [usage]
- Issues: [any found]
```

Deliver via Telegram message (short version) + full file for review.

## Deactivation

Night shift ends when:
1. User says to stop

On deactivation:
1. Compile summary.md if not done
2. Remove the cron job
3. Update state.json status to "completed"
4. Send morning summary via Telegram
5. Update HEARTBEAT.md (remove night shift tasks)
6. Review what was done, what to improve, and fix any issues
