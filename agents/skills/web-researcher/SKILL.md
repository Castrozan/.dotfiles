# Web Researcher Skill

Deep research on any topic using web search, page fetching, and structured summarization.

## When to Use
- User asks to research a topic, tool, technology, or concept
- User says "look into", "research", "find out about", "what's the latest on"
- Heartbeat tasks involving research or exploration
- Evaluating whether to adopt a tool, library, or service

## Research Process

### Phase 1: Discovery
1. **Web search** the topic with 2-3 varied queries:
   - Direct query: `"topic name"`
   - Contextual: `"topic name" review OR comparison OR alternative`
   - Recent: use `freshness: "pw"` or `"pm"` for trending topics
2. Collect top 5-10 URLs from results

### Phase 2: Deep Dive
3. **Fetch** the most promising 3-5 pages (prioritize: official docs, GitHub READMEs, comparison articles, HN discussions)
4. For GitHub repos, check:
   - Stars, last commit date, open issues count
   - README quality, license, installation method
   - NixOS/Nix package availability (`nix search nixpkgs#name`)
5. For tools/services, evaluate:
   - Self-hostable? Open source? Privacy-respecting?
   - Active maintenance? Community size?
   - Integration with existing stack (NixOS, Clawdbot, Obsidian)

### Phase 3: Synthesis
6. **Produce a structured report**:

```markdown
# Research: [Topic]

## TL;DR
One paragraph summary — what it is, whether it's worth using, key tradeoff.

## What It Is
- Description, origin, purpose
- Key features (bullet points)

## Evaluation
| Criteria | Rating | Notes |
|----------|--------|-------|
| Maturity | 🟢/🟡/🔴 | Version, age, stability |
| Activity | 🟢/🟡/🔴 | Last commit, contributors |
| Docs | 🟢/🟡/🔴 | Quality, completeness |
| NixOS | 🟢/🟡/🔴 | Packaged? Easy to add? |
| Privacy | 🟢/🟡/🔴 | Self-host? Data policy? |

## Alternatives
- [Alt 1] — how it compares
- [Alt 2] — how it compares

## Verdict
🔥 Must try / ⭐ Worth trying / 📝 Note for later / ⏭️ Skip

## Action Items
- [ ] Concrete next steps if adopting
```

### Phase 4: Memory
7. Log findings in `memory/YYYY-MM-DD.md` under a Research section
8. If the tool is worth trying, add to TOOLS.md or create a project folder

## Research Depth Levels

### Quick (1-2 min)
- Single web search + 1 page fetch
- One-paragraph verdict
- Use for: "is X any good?", quick tool checks

### Standard (5-10 min)
- 2-3 searches + 3-5 page fetches
- Full structured report
- Use for: "research X", tool evaluations, heartbeat research tasks

### Deep (15-30 min)
- 5+ searches, 8+ page fetches, GitHub repo analysis
- Comparison matrix with alternatives
- Code examples or config snippets if applicable
- Use for: "deep dive into X", adoption decisions, night shift research

## Tips
- **Always check HN** for discussion threads — they have the real opinions
- **GitHub stars alone don't tell the story** — check last commit date and issue response time
- **For NixOS users**: always check if there's a Nix package or if it needs manual packaging
- **Compare against what we already use** — is it better than current tooling?
- **Be opinionated** — don't just list facts, give a recommendation
- **Note pricing** — free tier limits, open source alternatives

## Example Queries to Run
For a tool called "example-tool":
1. `"example-tool"` — general info
2. `"example-tool" vs alternative` — comparisons
3. `site:news.ycombinator.com "example-tool"` — HN discussions
4. `"example-tool" nixos OR nix` — Nix packaging status
5. `"example-tool" self-host OR docker` — deployment options
