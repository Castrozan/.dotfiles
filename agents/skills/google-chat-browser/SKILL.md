---
name: google-chat-browser
description: Send and read Google Chat messages via browser automation or webhook. Use for DMs, spaces, or incoming webhook posts.
---

<commands>
Read history then reply — the typical workflow:
`google-chat-read-history "recipient name" [count]`
`google-chat-send-by-name "recipient name" "message"`
`google-chat-send-by-name "recipient name" "/path/to/image.png" --image`

Name matching is case-insensitive per-word — "vitor bonfante" matches "Vitor Vassoler Bonfante". Contact resolution tries sidebar, then "show all" expansion, then Google Chat's search bar as fallback. Images are sent via clipboard paste (wl-copy + Ctrl+V). Claude Code images live at `~/.claude/image-cache/{session-id}/{N}.png`, OpenClaw at `~/.openclaw/media/inbound/`.

`google-chat-browser-cli resolve-contact --name "recipient name"` resolves a contact name to a DM URL (sidebar → expand → search bar). Use when you need the URL without sending.

When you already have a space URL, use `google-chat-browser-cli send-message --space-url URL --message TEXT [--image PATH]` or `google-chat-browser-cli send-image --space-url URL --image PATH [--caption TEXT]`. For webhook URLs, prefer `google-chat-browser-cli send-webhook --webhook-url URL --message TEXT` — no browser session needed.
</commands>

<session>
Requires pinchtab running with an active Google Chat login. If `session-status` fails or commands report sign-in required, log in via pinchtab headed mode, complete sign-in at chat.google.com, then switch back to headless.
</session>
