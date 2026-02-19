---
name: twitter
description: Scrape X/Twitter posts, profiles, search results, followers, and trends. Use when user shares x.com or twitter.com URLs, asks to find tweets, check Twitter/X profiles, search X, monitor accounts, post tweets, or extract Twitter data.
---

<tool_selection>
Two backends. Default to Grok Search for search and analysis tasks. Use twikit-cli for raw JSON data, write operations (post, reply, like, retweet, DM), and personal account access (timeline, bookmarks, followers). When twikit breaks or cookies expire, fall back to Grok Search.
</tool_selection>

<grok_search>
Searches X and the web via xAI Responses API. Returns synthesized answers with citations. Only grok-4 family models support server-side search.

grok-search "query" for combined X+web search. Add --x-only for X-only, --web-only for web-only, --allowed-domains for domain filtering, --raw for full JSON. Costs ~$0.05-0.20 per search. API key configured via openclaw models auth or XAI_API_KEY env var.
</grok_search>

<twikit_cli>
Direct scraper via cookie-based auth. Free, returns raw JSON, supports write operations.

Setup: twikit-cli extract-cookies (reads from ~/.pinchtab/chrome-profile/, re-run if cookies expire).

Read: search "query" -n N [-p top], user USERNAME, user-tweets USERNAME -n N [-t replies], tweet ID, replies ID, thread ID, timeline -n N, trends, bookmarks -n N, followers/following USERNAME -n N.

Write: post "text" [--reply-to ID], like ID, retweet ID, bookmark ID, dm USER_ID "text".

Output is JSON arrays with id, text, created_at, user, favorite_count, retweet_count, view_count, url.

Files: cookies at ~/.config/twikit/cookies.json, credentials at ~/.secrets/x-{username,email,password} (agenix-managed), venv at ~/.local/share/twikit-venv/.
</twikit_cli>

<troubleshooting>
Cookies expired: twikit-cli extract-cookies. Twikit broken (X API change): use grok-search as fallback. Grok returns no results: check API key, ensure grok-4 model. "model not supported" error: Grok search requires grok-4 family only.
</troubleshooting>
