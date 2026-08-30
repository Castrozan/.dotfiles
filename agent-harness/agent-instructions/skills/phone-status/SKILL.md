---
name: phone-status
description: Report the phone's battery, charging, uptime, load, and storage over SSH with the phone-status CLI. Use for how the phone is doing, its battery, or its storage.
---

<execution>
Run `phone-status` (no arguments) and report the result. It SSHes to the phone over Tailscale and prints single-line
JSON with `battery`, `charging`, `uptime`, `load`, and `storage_used_pct`. Summarize those fields for the user.
</execution>

<unreachable_phone>
If it prints nothing, the SSH key is missing or the phone is unreachable on Tailscale; the script swallows stderr.
Diagnose with `ls -l /run/agenix/id_ed25519_phone` and `ssh phone uptime`.
</unreachable_phone>
