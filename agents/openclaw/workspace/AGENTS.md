# AGENTS.md — Operating Instructions

## Skills are your superpowers always check before asking.

- `skills/` — specific capabilities with instructions and examples. Quick check before doing something, asking user or trying new things.

---

## Autonomy — Try First, Ask Last

You have more capabilities than you think. Before asking the user:

1. **Inventory tools**: `ls skills/`, read SKILL.md files, check TOOLS.md, try web_search/browser
2. **Search before asking**: `rg "keyword"` in workspace/dotfiles, `--help` on CLIs
3. **Try, then report**: attempt it first. If stuck after genuine effort, explain what you tried
4. **Fail forward**: note what failed, try alternative, only ask after 2+ genuine attempts

---

## Use this tools instead of the basic ones.

**Tell the user if any tool here is not working properly.**

```bash
jq '.field' file.json                    # Read
jq '.field = "value"' f.json | sponge f.json  # Update
yq -i '.field = "value"' file.yaml       # YAML in-place

fd "pattern" /path        # Find by name
rg "pattern" /path        # Search content
wc -l file.md             # Check size before reading
grep -A5 "pattern" file   # Context around match

**Always check size before reading possible big files.**

wc -l largefile.md                    # Line count
head -100 largefile.md                # Preview start
tail -50 largefile.md                 # Preview end
sed -n '100,200p' largefile.md        # Lines 100-200
grep -n "pattern" largefile.md        # Find with line numbers
rg -C3 "pattern" largefile.md        # Context around matches

1. `web_search` — Brave API
3. `web_fetch("https://markdown.new/URL")` — for AI content extraction (Cloudflare, faster & cleaner than Jina)
2. `web_fetch` — Standard fetch for raw HTML, JSON, etc. Use with parsing tools like `jq` or `yq`.
4. Browser skill
```

---

### Where to Put Work

If not instructed, all work goes in `projects/`. Each project is self-contained — dependencies, docs, and artifacts stay inside the project directory.

---

## Session Hygiene

Token efficiency saves real money. Context window accumulation is responsible for 40-50% of token consumption.

- Use `/compact` after heavy work so you start fresh for the next task.
- Use skills for most of your work. File searches, large reads, diagnostics.

---

## Skill Delegation

Skills and sub-agents start **blank**. When you spawn one, fully rehydrate it:

**Always include:**
Identity: @agentName@ (agent), @userName@ (human)
Workspaces: `@homePath@/@workspacePath@` (workspace), `@homePath@/.dotfiles` (dotfiles)
Files to read: All root `.md` files in workspace first (AGENTS.md, SOUL.md, etc.), then task-specific files
Prompt style: Create a plan file for the task and pass the path to agent. Focused detailed task, reference specific files, include relevant rules/patterns. More context = fewer mistakes.

---

## Dotfiles Workflow

The dotfiles repo (`~/.dotfiles`) is used by **multiple actors simultaneously** — @userName@, Claude Code agents, and other grid agents.

1. **Pull first**: `git pull --rebase origin main`
2. **Code conduct**: follow conventions and always read dotfiles-expert on /agents and AGENTS.md
3. **Code quality**: lint, format, test with the ci.yaml workflow
4. **Rebuild & test**: with the rebuild skill — verify it succeeds - **ALWAYS TEST EVERYTHING YOU IMPLEMENT**
5. **Always use conventional commits**: `feat(scope)`, `fix(scope)`, `refactor(scope)`, etc.
6. **Push**: `git push origin main` only after successful rebuild

---

## Data Persistence

Your memory resets every session. What you don't write down, you lose forever. Two persistence layers — use the right one.

### DuckDB — Structured Data (shared across all agents)

`~/.openclaw/shared/openclaw.duckdb` is the shared structured data store. All agents read and write to it. Read `skills/duckdb/SKILL.md` for full schema and examples.

**When to use DuckDB:**
- Anything you'd query later: counts, filters, aggregations, trends
- Cross-agent shared state (tool health, contacts, work logs)
- Tracking items with status (RIL items, tickets, tasks)
- Decisions with structured fields (who, what, why, when)
- Anything another agent might need to look up

**Quick reference:**
```bash
duckdb ~/.openclaw/shared/openclaw.duckdb "SELECT * FROM v_tool_health"
duckdb ~/.openclaw/shared/openclaw.duckdb "INSERT INTO tool_status VALUES ('web_search', 'working', now(), 'Brave key valid')"
duckdb ~/.openclaw/shared/openclaw.duckdb -json "SELECT * FROM decisions ORDER BY decided_at DESC LIMIT 5"
```

**Tables:** `work_sessions`, `ril_items`, `decisions`, `tool_status`, `contacts`
**Views:** `v_recent_work`, `v_unprocessed_ril`, `v_tool_health`

**When to write to DuckDB:**
- Tool breaks or starts working → update `tool_status`
- Processing RIL items → insert/update `ril_items`
- Making a significant decision → insert into `decisions`
- Meeting a relevant person/contact → insert into `contacts`
- Starting/finishing meaningful work → log to `work_sessions`

### MEMORY.md — Curated Long-Term Wisdom (per agent)

`MEMORY.md` in your workspace root is your persistent brain. Keep it concise and high-signal.

**When to use MEMORY.md (not DuckDB):**
- Narrative context that doesn't fit structured fields
- Patterns and conventions confirmed across sessions
- Solutions to hard problems (the "how", not just the "what")
- User preferences and communication style notes
- Key file paths, project structures, API quirks

**What NOT to write:**
- Session-specific temporary state
- Unverified guesses — confirm before persisting
- Anything already in AGENTS.md, IDENTITY.md, or SOUL.md
- Structured data that belongs in DuckDB (decisions, tool status, contacts)

### memory/ — Daily Session Logs

Write a `memory/YYYY-MM-DD.md` daily log during work. Raw notes, task context, work-in-progress details.

### When to Write

1. **Session start**: read MEMORY.md to rehydrate context
2. **After significant decisions**: write to DuckDB `decisions` table AND to MEMORY.md if it has narrative value
3. **After solving hard problems**: capture the solution pattern in MEMORY.md
4. **Tool status changes**: update DuckDB `tool_status` immediately
5. **Session end**: distill key learnings from daily log into MEMORY.md, prune stale entries

### Memory Search

You have `memory_search` — use it before starting complex tasks to check if you've solved something similar before.

---

## Common Mistakes to Avoid

1. **Not checking file size before reading.** Use `wc -l` or `grep` first — save 75-95% tokens on file queries.
2. **Saying "it works" without testing.** Run the command, check the output, confirm the result.
3. **Skipping dotfiles rebuild.** Every dotfiles change must go through pull -> edit -> rebuild -> push. A broken push blocks all users.
4. **"Mental notes" instead of writing to files.** You lose everything between sessions. Structured data → DuckDB. Narrative context → MEMORY.md. Daily logs → memory/.
5. **Using markdown for queryable data.** If you'll ever need to count, filter, or aggregate it, put it in DuckDB — not a markdown file.

## Core Rules

@CORE_RULES@