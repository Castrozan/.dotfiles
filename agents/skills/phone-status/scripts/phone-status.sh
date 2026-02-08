#!/usr/bin/env bash
set -euo pipefail
SSH_KEY="/run/agenix/id_ed25519_phone"
HOST="phone"
TIMEOUT=5

ssh -i "$SSH_KEY" -o ConnectTimeout=$TIMEOUT -o StrictHostKeyChecking=no "$HOST" '
echo "{"
echo "  \"timestamp\": \"$(date -Iseconds)\","
echo "  \"battery\": $(cat /sys/class/power_supply/battery/capacity),"
echo "  \"charging\": \"$(cat /sys/class/power_supply/battery/status)\","
echo "  \"uptime\": \"$(uptime -p 2>/dev/null || uptime)\","
echo "  \"load\": \"$(cat /proc/loadavg | cut -d" " -f1-3)\","
echo "  \"storage_used_pct\": \"$(df /data 2>/dev/null | tail -1 | awk "{print \$5}")\""
echo "}"
' 2>/dev/null
