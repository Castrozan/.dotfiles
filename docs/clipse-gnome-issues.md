# Clipse on GNOME Wayland - Known Issues

## Problem Summary

Clipse clipboard manager has compatibility issues with GNOME on Wayland due to protocol differences.

## Root Cause

- GNOME uses its own Wayland clipboard protocol
- `wl-paste --watch` requires **wlroots data-control protocol** (only available on wlroots-based compositors like Sway, Hyprland)
- Running `wl-paste --watch` on GNOME returns: `Watch mode requires a compositor that supports the wlroots data-control protocol`

## Symptoms

- Screen flickering when polling-based workaround is used
- Keyboard input issues (Ctrl+C sends just "c")
- "wl-clipboard is ready" notification spam
- Service constantly restarting

## Attempted Solutions

1. **systemd service with `--listen-shell`**: Exits immediately on Wayland (only prints message)
2. **Polling-based listener**: Causes flickering and performance issues
3. **`wl-paste --watch` wrapper**: Doesn't work on GNOME (protocol not supported)

## Working Workaround

Use clipse TUI on-demand only (no background monitoring):
- Win+V opens clipse TUI
- Browse/paste from existing history
- **Limitation**: New clipboard items are NOT captured

## Alternatives

See `clipboard-manager-alternatives.md` for GNOME-compatible options.

## Long-term Solutions

1. Switch to wlroots compositor (Hyprland, Sway) - see `hyprland-migration.md`
2. Use GNOME-native clipboard manager (gpaste)
3. Contribute GNOME protocol support to clipse fork
