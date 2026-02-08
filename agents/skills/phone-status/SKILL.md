---
name: phone-status
description: Remote phone status over SSH. Use when checking phone battery, charging status, uptime, or storage.
---

# Phone Status -- Remote Phone Monitor

Checks phone status over SSH via Tailscale. Returns JSON with battery, charging, uptime, load, and storage.

## Usage

```bash
scripts/phone-status.sh
```

## Output

```json
{
  "timestamp": "2026-02-08T10:00:00-03:00",
  "battery": 85,
  "charging": "Discharging",
  "uptime": "up 3 days",
  "load": "0.50 0.30 0.20",
  "storage_used_pct": "45%"
}
```

## Requirements

- SSH key at `/run/agenix/id_ed25519_phone`
- Phone reachable as `phone` host (Tailscale)
