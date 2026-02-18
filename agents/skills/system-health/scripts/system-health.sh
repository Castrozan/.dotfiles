#!/usr/bin/env bash
# system-health.sh — Quick system health check for night shift / heartbeats
# Covers: gateway, services, disk, network, git status, temperatures
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

ok() { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }

echo -e "${BOLD}━━━ System Health Check ━━━${NC}"
echo -e "  $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo

# 1. OpenClaw Gateway (local)
echo -e "${BOLD}Gateway${NC}"
if curl -sf http://localhost:@gatewayPort@/health >/dev/null 2>&1; then
  ok "OpenClaw gateway responding (localhost:@gatewayPort@)"
elif pgrep -f "openclaw" >/dev/null 2>&1; then
  ok "OpenClaw gateway process running (health endpoint unreachable)"
else
  fail "OpenClaw gateway not responding"
fi

# 2. Remote agent gateways — read from agenix at runtime
GRID_HOSTS_FILE="/run/agenix/grid-hosts"
if [ -f "$GRID_HOSTS_FILE" ]; then
  for AGENT in $(jq -r 'keys[]' "$GRID_HOSTS_FILE"); do
    HOST_PORT=$(jq -r --arg a "$AGENT" '.[$a]' "$GRID_HOSTS_FILE")
    AGENT_CAP="$(echo "${AGENT:0:1}" | tr '[:lower:]' '[:upper:]')${AGENT:1}"
    PORT="${HOST_PORT##*:}"
    echo -e "${BOLD}${AGENT_CAP}${NC}"
    if curl -sf --connect-timeout 3 "http://${HOST_PORT}/health" >/dev/null 2>&1; then
      ok "${AGENT_CAP} gateway responding (port ${PORT})"
    else
      warn "${AGENT_CAP} gateway unreachable (machine may be off)"
    fi
  done
else
  warn "Grid hosts file not found: $GRID_HOSTS_FILE"
fi

# 3. Key services
echo -e "${BOLD}Services${NC}"
for svc in hey-@agentName@; do
  if systemctl --user is-active "$svc" >/dev/null 2>&1; then
    ok "$svc: active"
  else
    warn "$svc: inactive"
  fi
done

# 4. Pinchtab browser (CDP)
if curl -sf http://localhost:9222/json/version >/dev/null 2>&1; then
  ok "Pinchtab CDP: running (port 9222)"
else
  warn "Pinchtab CDP: not available"
fi

# 5. Disk usage
echo -e "${BOLD}Disk${NC}"
DISK_PCT=$(df -h / | awk 'NR==2{print $5}' | tr -d '%')
DISK_AVAIL=$(df -h / | awk 'NR==2{print $4}')
if [ "$DISK_PCT" -lt 80 ]; then
  ok "Root: ${DISK_PCT}% used (${DISK_AVAIL} free)"
elif [ "$DISK_PCT" -lt 90 ]; then
  warn "Root: ${DISK_PCT}% used (${DISK_AVAIL} free)"
else
  fail "Root: ${DISK_PCT}% used (${DISK_AVAIL} free) — CRITICAL"
fi

HOME_PCT=$(df -h /home | awk 'NR==2{print $5}' | tr -d '%')
HOME_AVAIL=$(df -h /home | awk 'NR==2{print $4}')
if [ "$HOME_PCT" -lt 80 ]; then
  ok "Home: ${HOME_PCT}% used (${HOME_AVAIL} free)"
elif [ "$HOME_PCT" -lt 90 ]; then
  warn "Home: ${HOME_PCT}% used (${HOME_AVAIL} free)"
else
  fail "Home: ${HOME_PCT}% used (${HOME_AVAIL} free) — CRITICAL"
fi

# 6. Memory
echo -e "${BOLD}Memory${NC}"
MEM_INFO=$(free -h | awk 'NR==2{printf "%s/%s (%.0f%%)", $3, $2, $3/$2*100}')
ok "RAM: $MEM_INFO"

# 7. Temperatures (if available)
if command -v sensors >/dev/null 2>&1; then
  echo -e "${BOLD}Temps${NC}"
  CPU_TEMP=$(sensors 2>/dev/null | grep -i 'Package\|Tctl\|Core 0' | head -1 | grep -oP '\+\K[0-9.]+' | head -1)
  if [ -n "$CPU_TEMP" ]; then
    TEMP_INT=${CPU_TEMP%.*}
    if [ "$TEMP_INT" -lt 70 ]; then
      ok "CPU: ${CPU_TEMP}°C"
    elif [ "$TEMP_INT" -lt 85 ]; then
      warn "CPU: ${CPU_TEMP}°C (warm)"
    else
      fail "CPU: ${CPU_TEMP}°C (HOT)"
    fi
  fi
fi

# 8. Uptime & load
echo -e "${BOLD}System${NC}"
UPTIME=$(uptime -p 2>/dev/null | head -1 || echo "unknown")
LOAD=$(cut -d' ' -f1-3 /proc/loadavg)
ok "Uptime: $UPTIME"
ok "Load: $LOAD"

# 9. Git status (workspace)
echo -e "${BOLD}Git (~/@workspacePath@)${NC}"
if git -C ~/@workspacePath@ rev-parse --git-dir >/dev/null 2>&1; then
  BRANCH=$(git -C ~/@workspacePath@ branch --show-current 2>/dev/null || echo "unknown")
  DIRTY=$(git -C ~/@workspacePath@ status --porcelain 2>/dev/null | wc -l)
  if [ "$DIRTY" -eq 0 ]; then
    ok "Branch: $BRANCH (clean)"
  else
    warn "Branch: $BRANCH ($DIRTY uncommitted changes)"
  fi
else
  warn "Not a git repo"
fi

# 10. Git status (dotfiles)
echo -e "${BOLD}Git (~/.dotfiles)${NC}"
if git -C ~/.dotfiles rev-parse --git-dir >/dev/null 2>&1; then
  BRANCH=$(git -C ~/.dotfiles branch --show-current 2>/dev/null || echo "unknown")
  DIRTY=$(git -C ~/.dotfiles status --porcelain 2>/dev/null | wc -l)
  if [ "$DIRTY" -eq 0 ]; then
    ok "Branch: $BRANCH (clean)"
  else
    warn "Branch: $BRANCH ($DIRTY uncommitted changes)"
  fi
else
  warn "Not a git repo"
fi

echo
echo -e "${BOLD}━━━ Done ━━━${NC}"
