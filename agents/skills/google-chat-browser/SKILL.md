---
name: google-chat-browser
description: Use when user needs to send Google Chat messages without Google Cloud project access, automate Google Chat from a persistent browser session, or post to an existing Google Chat incoming webhook.
---

<overview>
This skill provides a local Google Chat CLI that does not depend on creating a GCP project. It supports browser automation for any space or DM the signed-in browser session can access, plus direct webhook POSTs for spaces that already expose an incoming webhook URL.
</overview>

<commands>
Prepare the persistent browser session once:
`google-chat-browser-cli login --headed`

Check whether the stored session is ready:
`google-chat-browser-cli session-status`

Send to a Google Chat space or DM through browser automation:
`google-chat-browser-cli send-message --space-url 'https://chat.google.com/u/3/app/chat/AA...' --message 'message text'`

Send a longer message from a file or stdin:
`google-chat-browser-cli send-message --space-url URL --message-file /tmp/message.txt`
`printf 'message text' | google-chat-browser-cli send-message --space-url URL --message-file -`

Send through an existing incoming webhook:
`google-chat-browser-cli send-webhook --webhook-url 'https://chat.googleapis.com/v1/spaces/...' --message 'message text'`
</commands>

<delivery-choice>
Prefer `send-webhook` when the target space already has an incoming webhook URL. It is simpler and more reliable than browser automation, but it only works for spaces that already have that webhook configured. Use `send-message` for arbitrary rooms, spaces, and DMs visible to the signed-in browser session.
</delivery-choice>

<behavior>
`login` and `send-message` use a dedicated persistent browser profile in `~/.local/share/google-chat-browser-cli/chrome-profile/` by default. Run `login --headed` once, complete the Google sign-in flow in the opened browser window, then later `send-message` can run headless against the same stored session.

All commands print JSON to stdout and operational logs to stderr. Use `--headed` on `send-message` when debugging selectors or re-authentication.
</behavior>
