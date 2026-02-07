# Tool Patterns Reference

**This file is nix-managed (read-only). Read on-demand when you need tool syntax.**

## Browser Automation

- Primary: **OpenClaw managed browser** via `browser` tool.
- If a site is blocked by authwall: use **Google/SSO** in managed browser, then retry.
- For detailed automation guidance, read: `skills/playwright-mcp/SKILL.md` (canonical browser skill).
- For avatar demos: check `skills/avatar/SKILL.md` for browser/meeting notes.

**Tell the user as a big warning if any tool here is not working properly.**

## JSON/YAML

```bash
jq '.field' file.json                    # Read
jq '.field = "value"' f.json | sponge f.json  # Update
yq -i '.field = "value"' file.yaml       # YAML in-place
```

## File Search

```bash
fd "pattern" /path        # Find by name
rg "pattern" /path        # Search content
wc -l file.md             # Check size before reading
grep -A5 "pattern" file   # Context around match
```

## Large File Handling

**Always check size before reading unknown files.** One bloated read can waste more tokens than the entire rest of the session.

```bash
wc -l largefile.md                    # Line count
head -100 largefile.md                # Preview start
tail -50 largefile.md                 # Preview end
sed -n '100,200p' largefile.md        # Lines 100-200
grep -n "pattern" largefile.md        # Find with line numbers
rg -C3 "pattern" largefile.md        # Context around matches
```

**Rule of thumb:** If a file might be >500 lines, check first. If >1000 lines, never read it whole — search or paginate.

## Web Research (priority order)

1. `web_search` — Brave API
2. `web_fetch` — HTTP + readability
3. `web_fetch("https://r.jina.ai/URL")` — Jina Reader
4. Browser — dynamic sites only

## Git

```bash
git add specific-file.nix  # Never git add -A
# Dotfiles: pull -> rebuild -> push
```

## NixOS

- Use the /rebuild skill or .dotfiles/bin/rebuild for system rebuilds

## Base System

- **Browser**: `brave` (CDP 9222) / `openclaw` (CDP 18800)
- **Paths**: sudo at `/run/wrappers/bin`, packages at `/run/current-system/sw/bin`
- **Vault**: `@homePath@/vault/`
