---
name: phone-status
description: Query the user's phone over SSH (Tailscale) for battery percentage, charging state, uptime, load average, and storage usage. Returns JSON. Requires agenix-managed SSH key at /run/agenix/id_ed25519_phone and the phone reachable as the "phone" host.
---

<usage>
Run `scripts/phone-status.sh`. No arguments, no flags - the script is hard-wired to the phone host and SSH key path. Output is single-line JSON suitable for jq.
</usage>

<failure_modes>
SSH key missing or phone unreachable on Tailscale: the script swallows stderr and prints nothing. Check `ls -l /run/agenix/id_ed25519_phone` and `ssh phone uptime` to diagnose.
</failure_modes>
