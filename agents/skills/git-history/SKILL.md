---
name: git-history
description: Search git history efficiently via layered dump-to-file + fast text search. Use when searching commit history, finding when code changed, tracing feature evolution, or investigating past decisions. Replaces repeated git log --grep calls.
---

<search_strategy>
Never use repeated `git log --grep` or `git log -G` for exploratory search — each call rescans the full git object store. Instead, dump once to /tmp and search the dump with Grep (ripgrep). One dump, unlimited instant searches.

Three layers, escalate only when needed:

**Layer 1 — Titles + file paths** (default, always start here)
Run: `git-history.py dump` then search the file at `git-history.py path`.
Contains: commit hash, subject, body, and every changed file path per commit.
File paths catch what keywords miss — `home/modules/browser/` finds browser work even if the commit says "fix port conflict".

**Layer 2 — Full patches** (actual code changes)
Run: `git-history.py dump --layer 2` then search `git-history.py path --layer 2`.
Contains: every line of code ever added or removed. Larger file (~20MB for a 3k-commit repo) but grep is still instant (<50ms).
Use when: layer 1 didn't find enough, or you need to see what the actual code change was.

**Layer 3 — Scoped deep-dive** (targeted, use git directly)
For specific paths: `git log --all -- path/to/dir/`
For function evolution: `git log -L :functionName:file.ext`
For string introduction: `git log -S "exact_string" --all`
Use when: you've identified the area from layers 1-2 and need precise history.
</search_strategy>

<search_technique>
Search broad first, then narrow. Use multiple keyword variants in one grep — the commit message may say "browser" but the file path says "chrome" and the diff says "cdp". Cast a wide net:

```
grep -i "browser\|chrome\|cdp\|playwright\|devtools" /tmp/gitlog-*.txt
```

When searching layer 1, file paths are the highest-signal data — they don't suffer from terse commit messages. A commit touching `home/modules/openclaw/browser-use/` is about browser automation regardless of what the subject line says.

When searching layer 2 (patches), look for function names, variable names, config keys, error messages — things that appear in code but never in commit messages.
</search_technique>

<cache_behavior>
Cache files live in `/tmp/gitlog-{reponame}-{hash}-L{1,2}.txt`. Auto-invalidated when HEAD changes or file is older than 1 hour. Use `--force` to refresh manually. Use `git-history.py info` to check cache status. Cache is per-repo — works across multiple repos simultaneously.
</cache_behavior>

<when_not_to_use>
Skip this skill for simple, targeted lookups where you already know what you're looking for:
- `git log -1 HEAD` (last commit)
- `git blame file` (line-level authorship)
- `git show <hash>` (specific known commit)

These are fast single queries that don't benefit from the dump pattern.
</when_not_to_use>
