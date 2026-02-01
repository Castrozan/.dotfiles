# ReadItLater Processor — Clawdbot Skill

Automatically process, summarize, and organize your Obsidian ReadItLater inbox. Turns a pile of saved links into actionable knowledge.

## What It Does

When triggered (via heartbeat or manual), this skill:

1. **Scans** your Obsidian ReadItLater inbox folder for unprocessed items
2. **Reads** each item and classifies it (tweet, article, GitHub repo, video, note, other)
3. **Summarizes** the content with key takeaways
4. **Tags** items with relevant Obsidian tags (#tool, #ai, #nixos, #dev, etc.)
5. **Rates** relevance (🔥 must-read, ⭐ interesting, 📝 reference, ⏭️ skip)
6. **Marks processed** with `#agent-work-done` tag
7. **Generates a digest** — a single markdown file with all processed items summarized

## Configuration

Set these in your HEARTBEAT.md or pass as context:

```yaml
readitlater:
  inbox_path: "/path/to/vault/ReadItLater Inbox/"
  output_path: "/path/to/vault/ReadItLater Digests/"
  batch_size: 20                    # items per run
  skip_patterns:                    # skip these by filename
    - "Youtube -"                   # YouTube saves (can't extract content)
    - "Article 20"                  # Instagram/dead links
  tag_processed: "#agent-work-done" # tag added to processed items
  relevance_filter: "dev"           # focus: dev, ai, general, all
```

## Usage

### In HEARTBEAT.md
```markdown
## Task: Process ReadItLater
Process unprocessed items from Obsidian ReadItLater inbox.
- Path: /home/user/vault/ReadItLater Inbox/
- Batch: 20 items per cycle
- Focus on: dev tools, AI, NixOS content
- Skip: YouTube saves, Instagram links
- Tag processed items with #agent-work-done
- Write digest to memory/YYYY-MM-DD.md
```

### Manual Trigger
Just tell your Clawdbot: "Process my ReadItLater inbox" and it will follow this skill.

## Processing Logic

### Item Classification
| Type | Detection | Processing |
|------|-----------|------------|
| **Tweet** | `[[Tweet]]` tag or twitter.com URL | Extract author, quote, key claim |
| **GitHub Repo** | `github.com` URL, `[[Article]]` | Stars, language, what it does, install method |
| **Article** | `[[Article]]` tag | Title, source, TL;DR (3 sentences max) |
| **Note/Voice** | `[[Textsnippet]]` tag | Transcription context, action items |
| **Video** | YouTube URL | Note as unwatchable from CLI, skip or extract title |
| **Dead Link** | Empty content or error page | Mark as dead, skip |

### Relevance Scoring
- 🔥 **Must-read**: Directly useful (tools to install, techniques to apply, money opportunities)
- ⭐ **Interesting**: Worth knowing about (trends, new projects, ecosystem news)
- 📝 **Reference**: Save for later lookup (documentation, tutorials, configs)
- ⏭️ **Skip**: Not relevant (entertainment, broken links, off-topic)

### Output: Digest Format
```markdown
# ReadItLater Digest — YYYY-MM-DD

## 🔥 Must-Read
### [Tool Name](url)
**Type**: GitHub Repo | **Stars**: 5.2k | **Language**: Rust
One-line summary of what it does and why you care.
**Action**: `cargo install tool-name`

## ⭐ Interesting
### [Article Title](url)
**Source**: blog.example.com
TL;DR in 2-3 sentences.

## 📝 Reference
- [Config Guide](url) — How to set up X with Y
- [API Docs](url) — Reference for Z integration

## ⏭️ Skipped (12 items)
- 8 YouTube videos (can't process from CLI)
- 3 Instagram reels (no content extractable)
- 1 dead link
```

## Integration with Other Skills

### Night Shift
Add as a rotation task in the night-shift cycle. Processes 20 items per heartbeat, tracks progress.

### Morning Brief
Feed the digest into a morning summary: "While you slept, I processed 20 saved items. Here are the 3 you should look at..."

### QMD Search
After processing, items are indexed by qmd for fast semantic search across your entire vault.

## Tips

- **Batch size 20** is a sweet spot — enough to make progress, not so much it burns context
- **Skip YouTube** unless you have transcript extraction set up (Readeck can do this)
- **Tag immediately** after reading, even if summary is brief — prevents re-processing
- **Voice notes** (Textsnippet) often contain Lucas's TODO items — flag these as action items
- **GitHub repos**: check stars count and last commit date to gauge if worth installing

## Requirements
- Obsidian vault with ReadItLater plugin (or any folder of markdown files)
- Clawdbot with file read/write access
- Optional: web_fetch for enriching summaries of linked content
- Optional: qmd for post-processing search indexing
