#!/usr/bin/env bash
echo -n "  Opening browser with avatar renderer..."
DISCOVERED_CDP_PORT=$(python3 "$LAUNCHER_DIRECTORY/browser/runtime.py" start "http://localhost:@avatarRendererPort@")
if [[ -n "$DISCOVERED_CDP_PORT" ]]; then
	echo -e " ${GREEN}OK${NC} (CDP port: $DISCOVERED_CDP_PORT)"
else
	echo -e " ${RED}FAILED${NC} (owned browser unavailable)"
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
