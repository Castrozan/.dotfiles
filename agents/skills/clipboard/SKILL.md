---
name: clipboard
description: Read and write the system clipboard. Use when transferring text between applications, capturing copied content, or programmatically setting clipboard contents.
---

<execution>
Run: scripts/clipboard.sh read [--type MIME]
Run: scripts/clipboard.sh write "content" [--type MIME]

scripts/clipboard.sh read                     # read current clipboard text
scripts/clipboard.sh write "hello world"      # set clipboard to text
scripts/clipboard.sh read --type image/png    # read clipboard image (saves to /tmp, prints path)
scripts/clipboard.sh write --type image/png < file.png  # copy image to clipboard
</execution>

<environment>
Wayland-only. Requires WAYLAND_DISPLAY. The script auto-sets WAYLAND_DISPLAY=wayland-1 and XDG_RUNTIME_DIR if missing.
</environment>
