---
name: twikit
description: Scrape X/Twitter posts, profiles, search results, followers, and trends. Use when user asks to find tweets, check Twitter profiles, search X, monitor accounts, or extract Twitter data.
---

# X/Twitter (twikit-cli)

Agent-optimized CLI for X/Twitter. All commands output JSON. Cookie-based auth from browser session.

## First-Time Setup

Extract cookies from the agent browser (already logged into X):

```bash
twikit-cli extract-cookies
```

This reads cookies from `~/.local/share/pw-browser/` and saves to `~/.config/twikit/cookies.json`. One-time operation, cookies persist.

If cookies expire, run `extract-cookies` again.

## Read Operations

### Search tweets
```bash
twikit-cli search "AI agents" -n 10
twikit-cli search "NixOS" -n 5 -p top
twikit-cli search "from:elonmusk AI" -n 10
twikit-cli search "AI agents" -p media -n 5
```

### User profile
```bash
twikit-cli user elonmusk
```

### User tweets
```bash
twikit-cli user-tweets elonmusk -n 10
twikit-cli user-tweets elonmusk -t replies -n 10
twikit-cli user-tweets elonmusk -t media -n 10
twikit-cli user-tweets elonmusk -t likes -n 10
```

### Single tweet + replies
```bash
twikit-cli tweet 1234567890
twikit-cli replies 1234567890
```

### Timeline, trends, bookmarks
```bash
twikit-cli timeline -n 20
twikit-cli trends
twikit-cli bookmarks -n 20
```

### Followers / following
```bash
twikit-cli followers username -n 20
twikit-cli following username -n 20
```

## Write Operations

```bash
twikit-cli post "Hello from the terminal"
twikit-cli post "Reply text" --reply-to 1234567890
twikit-cli like 1234567890
twikit-cli retweet 1234567890
twikit-cli bookmark 1234567890
twikit-cli dm USER_ID "Hello there"
```

## Agent Patterns

```bash
# Parse with jq
twikit-cli search "query" -n 5 | jq '.[] | {user: .user.username, text: .text}'
twikit-cli user-tweets username -n 10 | jq '.[].url'
twikit-cli user username | jq '.followers_count'

# Read a thread
twikit-cli tweet TWEET_ID && twikit-cli replies TWEET_ID
```

## Output Format

JSON arrays (lists) or objects (single items):

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

## Files

- **Cookies:** `~/.config/twikit/cookies.json`
- **Credentials:** `~/.secrets/x-{username,email,password}` (agenix-managed, fallback login)
- **Venv:** `~/.local/share/twikit-venv/`

## Links

- https://github.com/d60/twikit
- https://twikit.readthedocs.io/en/latest/twikit.html
