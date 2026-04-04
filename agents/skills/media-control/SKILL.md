---
name: media-control
description: Control media playback and system volume — play, pause, toggle, next, previous, status, and volume adjustment via playerctl and wpctl.
---

Run `scripts/media-control.sh` from this skill's directory with one of the following subcommands:

- `play` / `pause` / `toggle` — start, stop, or toggle playback via playerctl
- `next` / `prev` — skip tracks via playerctl
- `status` — print `Artist - Title [Playing|Paused]`
- `volume VALUE` — set system volume; VALUE is 0–100 (absolute) or +N/-N (relative, e.g. `+5`, `-10`)
