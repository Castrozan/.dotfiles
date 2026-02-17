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

## Common Mistakes to Avoid

1. **Not checking file size before reading.** Use `wc -l` or `grep` first — save 75-95% tokens on file queries.
2. **Saying "it works" without testing.** Run the command, check the output, confirm the result.
3. **Skipping dotfiles rebuild.** Every dotfiles change must go through pull -> edit -> rebuild -> push. A broken push blocks all users.
4. **"Mental notes" instead of writing to files.** You lose everything between sessions. Write to TOOLS.md, memory/, or MEMORY.md.

## Core Rules

@CORE_RULES@