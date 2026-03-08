---
name: clipboard
description: Read and write the system clipboard. Use when transferring text between applications, capturing copied content, or programmatically setting clipboard contents.
---

<usage>
Run scripts/clipboard.sh read|write. Write takes content as argument. Both accept --type MIME for non-text content.
</usage>

<pitfalls>
Wayland-only — requires socket access. When reading image types (--type image/png), output is saved to /tmp and path is printed (not raw binary to stdout). wl-paste exits non-zero when clipboard is empty — script returns empty string instead of failing. wl-copy holds clipboard until another copy replaces it — the process forks to background, don't worry about dangling processes.
</pitfalls>
