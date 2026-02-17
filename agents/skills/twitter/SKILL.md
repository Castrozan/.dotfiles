---
name: twitter
description: Interact with X/Twitter — search, read profiles, post, and monitor. Routes between twikit (free scraper, raw data, write ops) and Grok Search (reliable API, synthesized answers, combined web+X). Use when user asks about tweets, Twitter trends, X profiles, posting, or anything X/Twitter related.
---

# X/Twitter

Unified skill for all X/Twitter interactions. Two backends, each with strengths.

## Decision Table

| Task | Tool | Why |
|------|------|-----|
| Search tweets / trending topics | **Grok Search** | Reliable, synthesized, includes web context |
| Raw tweet data as JSON | **twikit-cli** | Structured data with IDs, counts, URLs |
| Post / reply / like / retweet | **twikit-cli** | Only tool with write access |
| User profile details | **twikit-cli** | Raw JSON with follower counts, bio |
| "What are people saying about X" | **Grok Search** | Synthesized analysis with citations |
| Timeline / bookmarks / followers | **twikit-cli** | Personal account data |
| Combined web + X research | **Grok Search** | Searches both in one call |
| Twikit broken / cookies expired | **Grok Search** | Fallback, always works |

**Default**: Use Grok Search for search/analysis. Use twikit-cli for raw data, write operations, and personal account access.

---

## Grok Search (xAI Responses API)

Searches X/Twitter and the web via xAI's Grok model with live search. Returns synthesized answers with citations. Requires xAI API key (configured in auth-profiles).

**Only grok-4 family models support server-side search.** Uses `/v1/responses` endpoint (not `/v1/chat/completions`).

### Usage

```bash
grok-search "What's trending about NixOS on Twitter?"
grok-search --x-only "OpenClaw latest updates"
grok-search --web-only "Claude Code tutorials"
grok-search --allowed-domains "github.com,x.com" "AI agents"
grok-search --raw "query" | jq '.output'
```

### Options

| Flag | Description |
|------|-------------|
| `--x-only` | Focus only on X/Twitter posts |
| `--web-only` | Focus only on web results |
| `--allowed-domains d1,d2` | Restrict to specific domains (max 5) |
| `--excluded-domains d1,d2` | Exclude specific domains (max 5) |
| `--model <model>` | Override model (default: grok-4-latest) |
| `--raw` | Output full JSON response |

### Cost

~$0.05-0.20 per search (grok-4 token pricing). Use for high-value queries, not bulk scraping.

### Setup

API key configured via:
```bash
openclaw models auth paste-token --provider xai
```
Or set `XAI_API_KEY` environment variable.

---

## twikit-cli (Scraper)

Direct X/Twitter scraper via cookie-based auth. Free, returns raw JSON, supports write operations.

### Setup

```bash
twikit-cli extract-cookies
```

Reads cookies from `~/.local/share/pw-browser/` and saves to `~/.config/twikit/cookies.json`. Re-run if cookies expire.

### Read Operations

```bash
twikit-cli search "AI agents" -n 10
twikit-cli search "NixOS" -n 5 -p top
twikit-cli search "from:elonmusk AI" -n 10
twikit-cli user elonmusk
twikit-cli user-tweets elonmusk -n 10
twikit-cli user-tweets elonmusk -t replies -n 10
twikit-cli tweet 1234567890
twikit-cli replies 1234567890
twikit-cli thread 1234567890
twikit-cli timeline -n 20
twikit-cli trends
twikit-cli bookmarks -n 20
twikit-cli followers username -n 20
twikit-cli following username -n 20
```

### Write Operations

```bash
twikit-cli post "Hello from the terminal"
twikit-cli post "Reply text" --reply-to 1234567890
twikit-cli like 1234567890
twikit-cli retweet 1234567890
twikit-cli bookmark 1234567890
twikit-cli dm USER_ID "Hello there"
```

### Output Format

JSON arrays/objects:
```json
[{
  "id": "123",
  "text": "Tweet content",
  "created_at": "2026-02-16T10:00:00",
  "user": {"id": "456", "name": "Name", "username": "handle"},
  "favorite_count": 42,
  "retweet_count": 7,
  "reply_count": 3,
  "view_count": 1200,
  "url": "https://x.com/handle/status/123"
}]
```

### Agent Patterns

```bash
twikit-cli search "query" -n 5 | jq '.[] | {user: .user.username, text: .text}'
twikit-cli user username | jq '.followers_count'
```

### Files

- **Cookies:** `~/.config/twikit/cookies.json`
- **Credentials:** `~/.secrets/x-{username,email,password}` (agenix-managed)
- **Venv:** `~/.local/share/twikit-venv/`

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| twikit cookies expired | `twikit-cli extract-cookies` |
| twikit broken (X API change) | Use `grok-search` as fallback |
| Grok returns no results | Check API key, ensure grok-4 model |
| "model not supported" error | Grok search requires grok-4 family only |
