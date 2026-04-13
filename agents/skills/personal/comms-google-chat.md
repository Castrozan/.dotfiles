<scripts>
google-chat-read-history and google-chat-send-by-name for the typical read-then-reply workflow. google-chat-browser-cli for lower-level operations (resolve contacts, send to space URLs, webhooks). Run each with --help for usage.
</scripts>

<traps>
Name matching is case-insensitive per-word. Contact resolution tries sidebar first, then "show all" expansion, then Google Chat's search bar as fallback. Images are sent via clipboard paste (wl-copy + Ctrl+V). Claude Code images live at ~/.claude/image-cache/{session-id}/.
</traps>

<session_requirement>
Requires pinchtab running with an active Google Chat login. If commands report sign-in required, log in via pinchtab headed mode at chat.google.com, then switch back to headless.
</session_requirement>
