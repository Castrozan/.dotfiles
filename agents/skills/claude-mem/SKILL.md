# claude-mem — Persistent Memory for Claude Code

## What It Does

claude-mem gives Claude persistent memory across sessions. It captures conversations, compresses context, and injects relevant memories when needed. Your long-term memory supplement.

## Installation

Already in `~/.dotfiles/nix/plugins.nix`. Enable:

```bash
cd ~/.dotfiles && git pull --rebase && ./bin/rebuild
```

Memory stored in `~/.local/share/claude-mem/`.

## How It Works

**Capture** → **Compress** → **Store** → **Inject**. Monitors sessions, distills key info, saves with tags, auto-injects relevant context via MCP.

## MCP Tools

### `memory_search` — Find memories
```bash
memory_search query="browser automation" limit=5
```

### `memory_store` — Save information
```bash
memory_store content="Preferred TTS voice is Nova" tags="tts,preferences"
```

### `memory_list` — List memories
```bash
memory_list limit=10
memory_list tag="tools"
```

### `memory_delete` — Remove memories
```bash
memory_delete id="mem_abc123"
```

## Usage Patterns

**After solving problems:**
```bash
memory_store content="Fixed Nix rebuild - run as non-root" tags="nix,fix"
```

**Before complex work:**
```bash
memory_search query="similar task"  # Check if done before
```

**Periodic cleanup:**
```bash
memory_list limit=50  # Review
memory_delete id="..."  # Clean outdated
```

## Best Practices

- Store actionable knowledge: commands, debugging wins, workflow tips
- Use descriptive tags for effective searches
- Complement files, don't replace: MEMORY.md is still curated truth
- Search before asking for help
- Clean up outdated memories regularly

## When to Use What

| claude-mem | MEMORY.md | Daily logs |
|---|---|---|
| Tool discoveries | Long-term wisdom | Session activity |
| Debugging wins | Personality notes | Raw transcripts |
| Quick reference | Curated memories | Timestamped events |

claude-mem = working memory. MEMORY.md = soul. Daily logs = journal.
