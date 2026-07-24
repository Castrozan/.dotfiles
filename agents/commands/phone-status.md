---
description: Report the phone's battery, charging state, uptime, load, and storage over SSH
---

Run `phone-status` (no arguments) and report the result. It SSHes to the phone over Tailscale and prints single-line
JSON with `battery`, `charging`, `uptime`, `load`, and `storage_used_pct`. Summarize those fields for the user.

If it prints nothing, the SSH key is missing or the phone is unreachable on Tailscale; the script swallows stderr.
Diagnose with `ls -l /run/agenix/id_ed25519_phone` and `ssh phone uptime`.
