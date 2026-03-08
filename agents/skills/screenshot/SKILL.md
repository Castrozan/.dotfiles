---
name: screenshot
description: Capture desktop, window, or region screenshots. Use when needing to see what's on screen, inspect UI state, debug visual issues, or read non-browser application content.
---

<execution>
Run: scripts/screenshot.sh [--region] [--active] [--output PATH]

scripts/screenshot.sh                          # full desktop
scripts/screenshot.sh --region                 # interactive region select (slurp)
scripts/screenshot.sh --active                 # focused window only
scripts/screenshot.sh --output /tmp/shot.png   # custom output path
</execution>

<output>
Prints the absolute path to the saved PNG. Default location: /tmp/screenshot-TIMESTAMP.png. Read the output path to view the image.
</output>

<environment>
Wayland-only. Requires WAYLAND_DISPLAY set. Agents running in tmux/SSH must export WAYLAND_DISPLAY=wayland-1 and XDG_RUNTIME_DIR=/run/user/UID. The script handles this automatically.
</environment>
