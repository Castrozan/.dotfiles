<usage>
Run scripts/media-control.sh with subcommands: status, play, pause, toggle, next, previous, volume VALUE, list. Pass --player NAME to target a specific player when multiple are active.
</usage>

<pitfalls>
Requires DBUS_SESSION_BUS_ADDRESS — script sets it automatically but agents in containers without D-Bus access will fail silently. playerctl auto-selects the "most relevant" player which may not be what you expect with multiple players running — use "list" first, then --player NAME. Volume values are 0.0-1.0 (not 0-100); prefix with +/- for relative adjustment. Some players (Brave/Chrome) expose MPRIS but ignore volume commands — use system volume (wpctl) instead for browser audio.
</pitfalls>
