---
name: google-chat-browser
description: Use when user needs to send Google Chat messages without Google Cloud project access, automate Google Chat from a persistent browser session, or post to an existing Google Chat incoming webhook.
---

<overview>
This skill provides a local Google Chat CLI backed by pinchtab's persistent browser session. It supports browser automation for any space or DM the signed-in session can access, plus direct webhook POSTs for spaces with an incoming webhook URL.
</overview>

<commands>
Check whether the pinchtab session has Google Chat access:
`google-chat-browser-cli session-status`

Send to a Google Chat space or DM through browser automation:
`google-chat-browser-cli send-message --space-url 'https://chat.google.com/u/3/app/chat/AA...' --message 'message text'`

Send a longer message from a file or stdin:
`google-chat-browser-cli send-message --space-url URL --message-file /tmp/message.txt`
`printf 'message text' | google-chat-browser-cli send-message --space-url URL --message-file -`

Send through an existing incoming webhook:
`google-chat-browser-cli send-webhook --webhook-url 'https://chat.googleapis.com/v1/spaces/...' --message 'message text'`
</commands>

<prerequisites>
Pinchtab must be running with an active Google Chat session. If not logged in:
1. `pinchtab-switch-mode headed`
2. Navigate to `https://chat.google.com/` and complete sign-in
3. `pinchtab-switch-mode headless`
</prerequisites>

<delivery-choice>
Prefer `send-webhook` when the target space already has an incoming webhook URL. It is simpler and more reliable than browser automation, but it only works for spaces that already have that webhook configured. Use `send-message` for arbitrary rooms, spaces, and DMs visible to the signed-in browser session.
</delivery-choice>

<behavior>
All browser commands use pinchtab's shared session at `http://localhost:9867`. No separate browser profile or Playwright installation is needed. The CLI navigates Google Chat within pinchtab's active tab, fills the message composer via JavaScript, and clicks send.

All commands print JSON to stdout and operational logs to stderr. Legacy flags (`--profile-dir`, `--browser-executable`, `--headed`, `--screenshot`) are accepted but ignored for backward compatibility.
</behavior>
