---
name: youtube
description: Search YouTube videos, manage playlists, add/remove videos. Use when user asks to find YouTube videos, manage playlists, add videos to playlists, or interact with YouTube via CLI.
---

<overview>
Agent-optimized CLI for YouTube. Search via yt-dlp (no auth). Playlist management via YouTube Data API v3 (OAuth2). All commands output JSON. Accepts both IDs and full YouTube URLs.
</overview>

<setup>
OAuth2 credentials needed for playlist operations only. Create OAuth 2.0 Client ID (Desktop application) in Google Cloud Console with YouTube Data API v3 enabled. Save credentials to ~/.config/youtube-cli/credentials.json. First playlist command opens browser for authorization.
</setup>

<search>
youtube-cli search "query" -n COUNT. No auth needed. Parse results with jq: youtube-cli search "query" -n 5 | jq '.[] | {id, title, url}'.
</search>

<playlists>
List playlists: youtube-cli playlists. List videos: youtube-cli playlist-list PLAYLIST_ID. Add videos: youtube-cli playlist-add PLAYLIST_ID VIDEO_ID1 VIDEO_ID2. Remove: youtube-cli playlist-remove PLAYLIST_ITEM_ID. Create: youtube-cli playlist-create "Name" -d "Description" -p public.
</playlists>

<video_info>
youtube-cli info VIDEO_ID (accepts URLs too).
</video_info>

<output_format>
JSON arrays with fields: id, title, url, channel, duration, view_count.
</output_format>

<files>
OAuth credentials: ~/.config/youtube-cli/credentials.json. Token: ~/.config/youtube-cli/token.json (auto-generated). Venv: ~/.local/share/youtube-cli-venv/.
</files>
