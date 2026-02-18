---
name: system-health
description: System health monitoring for heartbeats and night shifts. Use when checking system status, gateway health, disk usage, temperatures, or service status.
---

# System Health -- Monitoring Dashboard

Quick system health check covering gateway, services, disk, network, git status, and temperatures.

## Usage

```bash
scripts/system-health.sh
```

## Checks Performed

1. OpenClaw gateway (local + remote agents via grid-hosts)
2. Key systemd user services
3. Pinchtab CDP availability
4. Disk usage (root + home)
5. Memory usage
6. CPU temperatures
7. Uptime and load
8. Git status (workspace + dotfiles)
