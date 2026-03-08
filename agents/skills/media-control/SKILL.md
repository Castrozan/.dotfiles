---
name: media-control
description: Control media playback — play, pause, next, previous, volume, and query now-playing. Use when managing music, podcasts, or any MPRIS-compatible media player.
---

<execution>
Run: scripts/media-control.sh COMMAND [ARGS]

scripts/media-control.sh status               # show player, track, artist, album, position
scripts/media-control.sh play                  # resume playback
scripts/media-control.sh pause                 # pause playback
scripts/media-control.sh toggle               # play/pause toggle
scripts/media-control.sh next                  # next track
scripts/media-control.sh previous              # previous track
scripts/media-control.sh volume 0.8            # set volume to 80% (0.0 to 1.0)
scripts/media-control.sh volume +0.1           # increase volume 10%
scripts/media-control.sh volume -0.1           # decrease volume 10%
scripts/media-control.sh list                  # list active media players
</execution>

<players>
Controls the most relevant active MPRIS player (playerctl auto-detects). For multiple players, use --player NAME after the command. Common players: spotify, firefox, chromium, mpv, vlc.
</players>
