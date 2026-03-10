---
name: google-chat-browser
description: Send and read Google Chat messages via browser automation or webhook. Use for DMs, spaces, or incoming webhook posts.
---

<commands>
Read history then reply — the typical workflow:
`google-chat-read-history "recipient name" [count]`
`google-chat-send-by-name "recipient name" "message"`

Name matching is case-insensitive per-word — "vitor bonfante" matches "Vitor Vassoler Bonfante".

When you already have a space URL or need stdin/file input, use `google-chat-browser-cli send-message --space-url URL --message TEXT`. For spaces with a webhook URL, prefer `google-chat-browser-cli send-webhook --webhook-url URL --message TEXT` — no browser session needed.
</commands>

<session>
Requires pinchtab running with an active Google Chat login. If `session-status` fails or commands report sign-in required, log in via pinchtab headed mode, complete sign-in at chat.google.com, then switch back to headless.
</session>
