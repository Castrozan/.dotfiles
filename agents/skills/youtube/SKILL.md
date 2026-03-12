---
name: youtube
description: Search YouTube videos, manage playlists, add/remove videos. Use when user asks to find YouTube videos, manage playlists, add videos to playlists, or interact with YouTube via CLI.
---

<overview>
youtube-cli is an agent-optimized CLI for YouTube. Search via yt-dlp (no auth needed). Playlist management via YouTube Data API v3 (requires OAuth2). All commands output JSON. Run youtube-cli --help for all available commands.
</overview>

<setup_trap>
OAuth2 credentials needed for playlist operations only. Create OAuth 2.0 Client ID (Desktop application) in Google Cloud Console with YouTube Data API v3 enabled. Save to ~/.config/youtube-cli/credentials.json. First playlist command opens browser for authorization — must use headed mode.
</setup_trap>
