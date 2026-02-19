---
name: phone-status
description: Remote phone status over SSH. Use when checking phone battery, charging status, uptime, or storage.
---

<execution>
Run scripts/phone-status.sh. Returns JSON with battery percentage, charging state, uptime, load average, and storage usage. Requires SSH key at /run/agenix/id_ed25519_phone and phone reachable as "phone" host via Tailscale.
</execution>
