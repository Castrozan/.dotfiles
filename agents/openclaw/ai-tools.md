# AI-TOOLS.md — Tool Patterns & Base Configuration

Use the right tool for the job. Don't reinvent what's already available.

## Base System Configuration

### Browser
- **Default profile**: `brave` (Lucas's Brave via CDP on port 9222)
- **Isolated profile**: `openclaw` (managed browser on cdpPort 18800)
- Brave must be launched with `--remote-debugging-port=9222`

### Audio
- Local Whisper CLI transcription (Portuguese, tiny model)
- Path: `/run/current-system/sw/bin/whisper`
- First run downloads model

### System
- NixOS, Dell G15
- Dotfiles: `~/.dotfiles` (Flakes + Home Manager)
- Obsidian vault: `/home/zanoni/vault/`
- Setuid wrappers (sudo): `/run/wrappers/bin`
- System packages: `/run/current-system/sw/bin`
- User packages: `/etc/profiles/per-user/zanoni/bin`

---

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
```

**Use `yq` for YAML and JSON** — supports in-place edits natively.
```bash
yq -i '.status = "completed"' file.json
yq -i '.tasks[0].status = "done"' file.yaml
```

**Use `sponge`** (from moreutils) for in-place pipe writes.

### When to use Write vs jq/yq
| Scenario | Tool |
|----------|------|
| Create new JSON file | `Write` or `jq -n` |
| Update field in existing JSON | `jq` + `sponge` or `yq -i` |
| Create new markdown | `Write` |
| Edit markdown section | `Edit` (surgical replace) |
| Overwrite entire config | `Write` (intentional full replace) |

## File Search & Navigation

**`qmd`** for markdown collections:
```bash
qmd search "query" -n 5          # Fast BM25 search
qmd get "collection/path.md"     # Get specific file
```
Collections: `vault` (Obsidian), `openclaw` (workspace), `dotfiles` (NixOS config).

**`fd`** for finding files:
```bash
fd "pattern" /path               # Find by name
fd -e md                          # Find by extension
```

**`rg`** (ripgrep) for content search:
```bash
rg "pattern" /path               # Search content
rg -l "pattern"                   # List matching files only
rg -t nix "openclaw"             # Search by file type
```

## Bash Commands (Token Optimization)

**Use bash for file queries before reading** — save 75-95% tokens.

```bash
wc -l memory/2026-02-01.md           # Check size before reading
grep -i "telegram" memory/*.md        # Search for keywords
grep -A5 -B5 "pattern" file.md       # Context around match
ls -lt memory/ | head -5             # List recent files
sed -n '/^## Header/,/^## /p' f.md   # Extract sections
```

### When to use bash vs read
| Scenario | Tool |
|----------|------|
| Unknown file size | `wc -l` first |
| Searching for keywords | `grep` |
| Listing directories | `ls` or `fd` |
| File exists check | `test -f` |
| Small files (<100 lines) | `read` directly |
| Need full context | `read` |

## System & Process

```bash
systemctl --user status hey-cleber
journalctl --user -u hey-cleber -f

XDG_RUNTIME_DIR=/run/user/1000 wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.7
XDG_RUNTIME_DIR=/run/user/1000 wpctl set-mute @DEFAULT_AUDIO_SINK@ 0
```

## Git

**Conventional commits:** `git add specific-file.nix` (never `git add -A` or `.`)
**Dotfiles workflow:** pull → rebuild → test → push. Always.

## NixOS

```bash
/run/wrappers/bin/sudo nixos-rebuild switch --flake ~/.dotfiles#zanoni
nix search nixpkgs#package-name
nix flake show
```

## Web Research

**Priority order** (fastest/cheapest first):
1. `web_search` — Brave Search API (rate limit: 1 req/sec, 2K/month free)
2. `web_fetch` — HTTP GET + readability, no JS
3. **Jina Reader** — `web_fetch("https://r.jina.ai/URL")` — better extraction, free tier
4. Browser — only for dynamic sites, authenticated pages, complex interactions

Add 2s delays between sequential `web_search` calls. If rate limited, fall back to Jina.

## TTS / Audio Output

**Use `tts` tool** → returns MP3 path, then play with mpv.

**Always use `background: true`** for mpv playback (exec timeout kills otherwise):
```bash
XDG_RUNTIME_DIR=/run/user/1000 mpv --no-video --ao=pipewire /path/to/voice.mp3
```

**Full TTS flow:**
1. Generate: `tts(text="...")` → `MEDIA:/tmp/tts-xxx/voice-xxx.mp3`
2. Unmute: `wpctl set-mute @DEFAULT_AUDIO_SINK@ 0`
3. Volume: `wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.7`
4. Play: `exec(command="... mpv ...", background=true)`

## Sub-Agent Delegation

**Use `sessions_spawn`** for isolated work — each gets fresh context (no bloat).

**Craft specific prompts:** what to do, what tools to use, where to write output, what format.
