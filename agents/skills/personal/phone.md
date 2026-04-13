
<execution>
Run `agents/skills/phone-status/scripts/phone-status.sh` (the script lives in its original sibling directory, outside this umbrella). Returns JSON with battery percentage, charging state, uptime, load average, and storage usage. Requires SSH key at /run/agenix/id_ed25519_phone and phone reachable as "phone" host via Tailscale.
</execution>
