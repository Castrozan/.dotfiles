#!/usr/bin/env bash
# Avatar System Launcher
# Starts all components in the correct order

set -e

AVATAR_DIR="@homePath@/@workspacePath@/avatar"
LOG_DIR="/tmp/clever-avatar-logs"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

mkdir -p "$LOG_DIR"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   Avatar System - Launcher${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

is_running() {
    pgrep -f "$1" > /dev/null 2>&1
}

wait_for_port() {
    local port=$1
    local timeout=30
    local elapsed=0

    echo -n "  Waiting for port $port to be available..."
    while ! ss -tlnp 2>/dev/null | grep -q ":$port " && [ $elapsed -lt $timeout ]; do
        sleep 1
        elapsed=$((elapsed + 1))
    done

    if [ $elapsed -ge $timeout ]; then
        echo -e " ${RED}TIMEOUT${NC}"
        return 1
    else
        echo -e " ${GREEN}OK${NC}"
        return 0
    fi
}

# Step 1: Set up virtual audio devices
echo -e "${YELLOW}[1/4]${NC} Setting up virtual audio devices..."

if XDG_RUNTIME_DIR=/run/user/1000 pactl list sinks short | grep -q "AvatarSpeaker"; then
    echo -e "  ${GREEN}✓${NC} Virtual audio sink already exists"
else
    echo -n "  Creating virtual audio sink (AvatarSpeaker)..."
    if XDG_RUNTIME_DIR=/run/user/1000 pactl load-module module-null-sink \
        sink_name=AvatarSpeaker \
        sink_properties=device.description="Avatar_Speaker" > /dev/null 2>&1; then
        echo -e " ${GREEN}OK${NC}"
    else
        echo -e " ${RED}FAILED${NC}"
        echo -e "  ${YELLOW}⚠${NC}  Virtual audio is optional for testing"
    fi
fi

echo ""

# Step 2: Start Control Server via systemd
echo -e "${YELLOW}[2/4]${NC} Starting Avatar Control Server..."

if systemctl --user is-active --quiet avatar-control-server; then
    echo -e "  ${YELLOW}⚠${NC}  Control server is already running"
else
    systemctl --user start avatar-control-server
    echo -e "  ${GREEN}✓${NC} Control server started (systemd)"

    if wait_for_port 8765; then
        echo -e "  ${GREEN}✓${NC} WebSocket server ready on port 8765"
    else
        echo -e "  ${RED}✗${NC} WebSocket server failed to start"
        systemctl --user status avatar-control-server --no-pager
        exit 1
    fi

    if wait_for_port 8766; then
        echo -e "  ${GREEN}✓${NC} HTTP server ready on port 8766"
    else
        echo -e "  ${RED}✗${NC} HTTP server failed to start"
        exit 1
    fi
fi

echo ""

# Step 3: Start Avatar Renderer
echo -e "${YELLOW}[3/4]${NC} Starting Avatar Renderer..."

if is_running "avatar/renderer.*next"; then
    echo -e "  ${YELLOW}⚠${NC}  Renderer is already running"
else
    cd "$AVATAR_DIR/renderer"
    nohup npm run dev > "$LOG_DIR/avatar-renderer.log" 2>&1 &
    RENDERER_PID=$!
    echo -e "  ${GREEN}✓${NC} Avatar renderer started (PID: $RENDERER_PID)"
    echo -e "    Log: $LOG_DIR/avatar-renderer.log"

    if wait_for_port 3000; then
        echo -e "  ${GREEN}✓${NC} Renderer ready on http://localhost:3000"
    else
        echo -e "  ${RED}✗${NC} Renderer failed to start"
        tail -10 "$LOG_DIR/avatar-renderer.log"
        exit 1
    fi
fi

echo ""

# Step 4: Health Check
echo -e "${YELLOW}[4/4]${NC} Running health checks..."

echo -n "  Control server health endpoint..."
if curl -sf http://localhost:8766/health > /dev/null 2>&1; then
    echo -e " ${GREEN}OK${NC}"
else
    echo -e " ${RED}FAILED${NC}"
fi

echo -n "  Renderer HTTP endpoint..."
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo -e " ${GREEN}OK${NC}"
else
    echo -e " ${RED}FAILED${NC}"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   ✓ Avatar System Ready!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Services:${NC}"
echo -e "  • Control Server:  ws://localhost:8765"
echo -e "  • HTTP API:        http://localhost:8766"
echo -e "  • Avatar Renderer: http://localhost:3000"
echo ""
echo -e "${BLUE}Stop:${NC}"
echo -e "  ~/openclaw/scripts/stop-avatar.sh"
echo ""
