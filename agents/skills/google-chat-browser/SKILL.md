---
name: google-chat-browser
description: Use when user needs to send Google Chat messages without Google Cloud project access, automate Google Chat from a persistent browser session, or post to an existing Google Chat incoming webhook.
---

<overview>
This skill provides Google Chat messaging backed by pinchtab's persistent browser session. Send messages by recipient name or space URL, or via webhook.
</overview>

<commands>
Send a message by recipient name (easiest — resolves the DM automatically):
`google-chat-send-by-name "Vitor Bonfante" "hello from CLI"`

Send to a known space URL:
`google-chat-browser-cli send-message --space-url 'https://chat.google.com/app/chat/XXXXX' --message 'message text'`

Send from a file or stdin:
`google-chat-browser-cli send-message --space-url URL --message-file /tmp/message.txt`
`printf 'message text' | google-chat-browser-cli send-message --space-url URL --message-file -`

Send through an existing incoming webhook:
`google-chat-browser-cli send-webhook --webhook-url 'https://chat.googleapis.com/v1/spaces/...' --message 'message text'`

Check session status:
`google-chat-browser-cli session-status`
</commands>

<prerequisites>
Pinchtab must be running with an active Google Chat session. If not logged in:
1. `pinchtab-switch-mode headed`
2. Navigate to `https://chat.google.com/` and complete sign-in
3. `pinchtab-switch-mode headless`
</prerequisites>

<delivery-choice>
Prefer `send-webhook` when the target space already has an incoming webhook URL — simpler and more reliable. Use `google-chat-send-by-name` for DMs when you know the person's name. Use `google-chat-browser-cli send-message --space-url` when you already have the URL or need to target a group space.
</delivery-choice>

<behavior>
All browser commands use pinchtab's shared session at `http://localhost:9867`. No separate browser profile is needed.

`google-chat-send-by-name` navigates to the Google Chat home, finds the matching contact in the sidebar, clicks into their DM, then delegates to `google-chat-browser-cli send-message`. The name match is case-insensitive and partial — "vitor" matches "Vitor Vassoler Bonfante".

All commands print JSON to stdout and operational logs to stderr.
</behavior>
