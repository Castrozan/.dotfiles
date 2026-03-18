---
name: twitter
description: Scrape X/Twitter posts, profiles, search results, followers, and trends. Use when user shares x.com or twitter.com URLs, asks to find tweets, check Twitter/X profiles, search X, monitor accounts, post tweets, or extract Twitter data.
---

<tool_selection>
Two backends. Default to grok-search for search and analysis tasks — returns synthesized answers with citations (~$0.05-0.20 per search). Use twikit-cli for raw JSON data, write operations (post, reply, like, retweet, DM), and personal account access (timeline, bookmarks, followers). When twikit breaks or cookies expire, fall back to grok-search. Run each tool with --help for available commands and flags.
</tool_selection>

<auth_traps>
grok-search: requires grok-4 family models only for server-side search. API key configured via XAI_API_KEY env var or auth-profiles.json.

twikit-cli: cookie-based auth. Run twikit-cli extract-cookies to pull from pinchtab's Chrome profile. Re-run when cookies expire. Credentials managed by agenix.
</auth_traps>

<troubleshooting>
Cookies expired: twikit-cli extract-cookies. Twikit broken (X API change): use grok-search fallback. Grok returns no results: check API key, ensure grok-4 model. "model not supported": Grok search requires grok-4 family only.
</troubleshooting>
