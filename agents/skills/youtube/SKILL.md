---
name: youtube
description: Search YouTube videos, manage playlists, add/remove videos. Use when user asks to find YouTube videos, manage playlists, add videos to playlists, or interact with YouTube via CLI.
---

# YouTube CLI

Agent-optimized CLI for YouTube. Search (via yt-dlp, no auth) and playlist management (via YouTube Data API v3, OAuth2).

## First-Time Setup

OAuth2 credentials needed for playlist operations (search works without auth):

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use existing)
3. Enable **YouTube Data API v3**
4. Create OAuth 2.0 Client ID (Desktop application)
5. Download the JSON and save to `~/.config/youtube-cli/credentials.json`
6. First playlist command will open browser for authorization

## Search (no auth needed)

```bash
youtube-cli search "tony stark jarvis" -n 10
youtube-cli search "iron man jarvis scene" -n 5
```

## Playlist Operations (needs OAuth)

### List your playlists
```bash
youtube-cli playlists
```

### List videos in a playlist
```bash
youtube-cli playlist-list PLH7_WFgyjjobHQalW2rO8jRk4r_Yt38iO
youtube-cli playlist-list "https://www.youtube.com/playlist?list=PLH7_WFgyjjobHQalW2rO8jRk4r_Yt38iO"
```

### Add videos to a playlist
```bash
youtube-cli playlist-add PLH7_xxx VIDEO_ID1 VIDEO_ID2
youtube-cli playlist-add PLH7_xxx "https://www.youtube.com/watch?v=abc123"
```

### Remove videos from a playlist
```bash
youtube-cli playlist-remove PLAYLIST_ITEM_ID
```

### Create a playlist
```bash
youtube-cli playlist-create "My Playlist" -d "Description" -p public
```

## Video Info

```bash
youtube-cli info VIDEO_ID
youtube-cli info "https://www.youtube.com/watch?v=abc123"
```

## Agent Patterns

```bash
# Search and parse
youtube-cli search "query" -n 5 | jq '.[].title'
youtube-cli search "query" -n 5 | jq '.[] | {id, title, url}'

# Search then add to playlist
youtube-cli search "tony stark jarvis" -n 10 | jq -r '.[].id' | xargs youtube-cli playlist-add PLAYLIST_ID

# List playlist contents
youtube-cli playlist-list PLAYLIST_ID | jq '.[] | {title, url}'
```

## Output Format

All commands output JSON arrays or objects:

```json
[{
  "id": "abc123",
  "title": "Video Title",
  "url": "https://www.youtube.com/watch?v=abc123",
  "channel": "Channel Name",
  "duration": 180,
  "view_count": 50000
}]
```

## Files

- **OAuth credentials:** `~/.config/youtube-cli/credentials.json` (from Google Cloud Console)
- **OAuth token:** `~/.config/youtube-cli/token.json` (auto-generated after first auth)
- **Venv:** `~/.local/share/youtube-cli-venv/`

## Accepts Both IDs and URLs

All commands that take playlist or video IDs also accept full YouTube URLs. The CLI extracts the ID automatically.
