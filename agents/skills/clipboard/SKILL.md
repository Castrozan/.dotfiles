---
name: clipboard
description: Read, write, and monitor the system clipboard via wl-paste/wl-copy. Supports text and image types on Wayland.
---

<execution>
Run scripts/clipboard.sh from this skill's directory.

Subcommands:
- `read` — print clipboard contents to stdout. Use `--type text/plain` or `--type image/png` for specific MIME types. Image output is saved to /tmp and the path is printed.
- `write` — set clipboard contents. Pass text as argument or via stdin: `clipboard.sh write "text"` or `echo "text" | clipboard.sh write`
- `watch` — stream clipboard changes to stdout as they occur (wl-paste --watch). Runs until interrupted.
</execution>

<pitfalls>
Wayland-only — requires WAYLAND_DISPLAY socket access. wl-paste exits non-zero when clipboard is empty — script returns empty string instead of failing. wl-copy forks to background after writing; the process holds the selection until another copy replaces it — this is normal. Image types are written to /tmp/clipboard-TIMESTAMP.ext and the path is returned, not raw bytes.
</pitfalls>
