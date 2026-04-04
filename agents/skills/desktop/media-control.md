<execution>
Run `scripts/media-control.sh` with subcommand: `play`, `pause`, `toggle`, `next`, `prev`, `status`, or `volume VALUE`. Volume accepts 0-100 (absolute) or +N/-N (relative).
</execution>

<pitfalls>
Requires D-Bus session bus — script auto-sets DBUS_SESSION_BUS_ADDRESS. playerctl operates on the most recent MPRIS-capable player; if multiple players are running, the target may be unexpected. Volume uses wpctl (PipeWire) — absolute values are percentages, relative use +N/-N syntax.
</pitfalls>
