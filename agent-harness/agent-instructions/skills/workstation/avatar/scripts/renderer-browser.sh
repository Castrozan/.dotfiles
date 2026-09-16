#!/usr/bin/env bash
discover_cdp_port() {
	ss -tlnp 2>/dev/null |
		grep -E 'chromium|chrome' |
		grep -o '127\.0\.0\.1:[0-9]*' |
		head -1 |
		cut -d: -f2
	return
}

# Try pinchtab first, then fall back to launching Chrome directly
echo -n "  Opening browser with avatar renderer..."
if curl -sf --max-time 2 http://localhost:9867/health >/dev/null 2>&1; then
	curl -sf --max-time 2 -X POST http://localhost:9867/shutdown >/dev/null 2>&1 || true
	sleep 2
fi
rm -f ~/.pinchtab/chrome-profile/Singleton* 2>/dev/null || true
BRIDGE_HEADLESS=false pinchtab >/dev/null 2>&1 &
sleep 3

DISCOVERED_CDP_PORT=$(discover_cdp_port)

if [[ -z "$DISCOVERED_CDP_PORT" ]]; then
	# Pinchtab failed — launch Chrome directly with CDP
	chromium --remote-debugging-port=9222 --autoplay-policy=no-user-gesture-required "http://localhost:@avatarRendererPort@" >/dev/null 2>&1 &
	sleep 3
	DISCOVERED_CDP_PORT=$(discover_cdp_port)
fi

if [[ -n "$DISCOVERED_CDP_PORT" ]]; then
	echo -e " ${GREEN}OK${NC} (CDP port: $DISCOVERED_CDP_PORT)"
	# Navigate to renderer if not already there
	curl -sf "http://127.0.0.1:$DISCOVERED_CDP_PORT/json" 2>/dev/null |
		node -e "const d=require('fs').readFileSync('/dev/stdin','utf8');const t=JSON.parse(d);if(!t.find(p=>p.url.includes('localhost:@avatarRendererPort@')))process.exit(1)" 2>/dev/null ||
		curl -s -X POST http://localhost:9867/navigate -H "Content-Type: application/json" -d '{"url":"http://localhost:@avatarRendererPort@"}' >/dev/null 2>&1 || true
else
	echo -e " ${RED}FAILED${NC} (no browser with CDP available)"
fi

# Inject renderer bridge (connects ChatVRM to control server for lip sync)
if [[ -n "$DISCOVERED_CDP_PORT" ]]; then
	echo -n "  Injecting renderer bridge for lip sync..."
	sleep 3
	CDP_PORT="$DISCOVERED_CDP_PORT" \
		NODE_PATH="$AVATAR_DIR/control-server/node_modules" \
		BRIDGE_SCRIPT_PATH="$AVATAR_DIR/control-server/renderer-bridge.js" \
		node "$AVATAR_DIR/control-server/inject-bridge.js" 2>/dev/null &&
		echo -e " ${GREEN}OK${NC}" || echo -e " ${YELLOW}FAILED${NC}"
fi

echo ""
