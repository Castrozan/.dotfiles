# AI-TOOLS.md — Preferred Tools & Patterns

Use the right tool for the job. Don't reinvent what's already available.

## JSON/YAML Manipulation

**Use `jq` for JSON** — never rewrite entire JSON files with the Write tool.
```bash
# Read a field
jq '.currentTask' state.json

# Update a field in-place
jq '.status = "completed"' file.json | sponge file.json

# Append to array
jq '.items += [{"name": "new"}]' file.json | sponge file.json

# Delete a key
jq 'del(.oldKey)' file.json | sponge file.json

# Conditional update
jq '(.tasks[] | select(.id == "task-1")).status = "done"' file.json | sponge file.json
```

**Use `yq` for YAML and JSON** — supports in-place edits natively.
```bash
# In-place update (JSON or YAML)
yq -i '.status = "completed"' file.json
yq -i '.tasks[0].status = "done"' file.yaml

# Read a field
yq '.config.port' file.yaml
```

**Use `sponge`** (from moreutils) for in-place pipe writes:
```bash
# Instead of: jq '...' f.json > tmp && mv tmp f.json
jq '.x = 1' f.json | sponge f.json
```

### When to use Write vs jq/yq
| Scenario | Tool |
|----------|------|
| Create new JSON file | `Write` or `jq -n '{...}' > file.json` |
| Update field in existing JSON | `jq` + `sponge` or `yq -i` |
| Create new markdown file | `Write` |
| Edit markdown section | `Edit` (surgical text replace) |
| Overwrite entire config | `Write` (intentional full replace) |

## File Search & Navigation

**Use `qmd` for searching markdown collections:**
```bash
qmd search "query" -n 5          # Fast BM25 search
qmd get "collection/path.md"     # Get specific file
qmd status                        # Check indexed collections
```
Collections: `vault` (Obsidian), `clawd` (workspace), `dotfiles` (NixOS config).

**Use `fd` for finding files:**
```bash
fd "pattern" /path               # Find files by name
fd -e md                          # Find by extension
fd -t f "night-shift"            # Files only
```

**Use `ripgrep` (rg) for searching file contents:**
```bash
rg "pattern" /path               # Search content
rg -l "pattern"                   # List matching files only
rg -t nix "openclaw"             # Search by file type
```

## System & Process

**Use `systemctl --user` for services:**
```bash
systemctl --user status hey-cleber
systemctl --user restart hey-cleber
journalctl --user -u hey-cleber -f    # Follow logs
```

**Use `wpctl` for audio (PipeWire):**
```bash
XDG_RUNTIME_DIR=/run/user/1000 wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.7
XDG_RUNTIME_DIR=/run/user/1000 wpctl set-mute @DEFAULT_AUDIO_SINK@ 0
XDG_RUNTIME_DIR=/run/user/1000 wpctl status    # List all streams
```

## Git

**Use conventional commits:**
```bash
git add specific-file.nix         # Never git add -A or .
git commit -m "feat: add night shift skill"
```

**Dotfiles workflow:** pull → rebuild → test → push. Always.

## NixOS

**Rebuild:** `/run/wrappers/bin/sudo nixos-rebuild switch --flake ~/.dotfiles#zanoni`
**Search packages:** `nix search nixpkgs#package-name`
**Check flake:** `nix flake show`

## Web Research

**Priority order** (fastest/cheapest first):
1. `web_search` — Brave Search API, structured results (rate limit: 1 req/sec, 2K/month free)
2. `web_fetch` — HTTP GET + readability extraction, no JS. Good when you know the URL.
3. **Jina Reader** — `web_fetch("https://r.jina.ai/URL")` — better extraction than raw web_fetch, free tier.
4. Browser — only for dynamic sites (X/Twitter), authenticated pages, or complex interactions.

**Rate limit handling:** Brave free tier is 1 req/sec. Add 2s delays between sequential
`web_search` calls. If rate limited, fall back to Jina or web_fetch.

**Jina Reader** (free, no API key for page reading):
```
web_fetch("https://r.jina.ai/https://example.com")  # Extract any page as clean markdown
```
Note: Jina Search (`s.jina.ai`) requires an API key. Page reading (`r.jina.ai`) is free.

**When using browser:**
- Light mode (single tab) for browser-use/Playwright
- Kill all Brave windows first
- Close browser when done — don't leave it open

## TTS / Audio Output

**Use `tts` tool** → returns MP3 path, then play with mpv.

**CRITICAL: Always use `background: true`** for mpv playback. Without it, the exec
timeout kills the process before audio finishes (SIGKILL).

```bash
# Correct — background mode, plays to completion
exec(command="XDG_RUNTIME_DIR=/run/user/1000 mpv --no-video --ao=pipewire /path/to/voice.mp3", background=true)
```

**Full TTS flow:**
1. Generate: `tts(text="...")` → returns `MEDIA:/tmp/tts-xxx/voice-xxx.mp3`
2. Unmute: `XDG_RUNTIME_DIR=/run/user/1000 wpctl set-mute @DEFAULT_AUDIO_SINK@ 0`
3. Volume: `XDG_RUNTIME_DIR=/run/user/1000 wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.7`
4. Play: `exec(command="XDG_RUNTIME_DIR=/run/user/1000 mpv --no-video --ao=pipewire <file>", background=true)`

**Do NOT:**
- Pass explicit `timeout` shorter than audio duration
- Use `yieldMs` with short values — let it background immediately

If music is playing, lower Brave volume first (see TOOLS.md for stream IDs).

## Sub-Agent Delegation

**Use `sessions_spawn`** for isolated work:
- Each sub-agent gets fresh context (no bloat)
- Results are announced back to main session
- Use for: research, builds, processing, analysis

**Craft specific prompts** — tell the sub-agent exactly:
1. What to do
2. What tools to use
3. Where to write output
4. What format to use
