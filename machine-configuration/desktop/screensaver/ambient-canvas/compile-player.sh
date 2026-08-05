#!/usr/bin/env bash
ambientCanvasPlayerSourceStamp="$AMBIENT_CANVAS_PLAYER_SOURCES_DIR $(/usr/bin/swiftc --version 2>/dev/null | head -1) ${AMBIENT_CANVAS_PLAYER_COMPILE_RECIPE_HASH:-}"
ambientCanvasPlayerSourceStampPath="$AMBIENT_CANVAS_PLAYER_BINARY_PATH.sourcehash"
if [ -x "$AMBIENT_CANVAS_PLAYER_BINARY_PATH" ] && [ "$(cat "$ambientCanvasPlayerSourceStampPath" 2>/dev/null)" = "$ambientCanvasPlayerSourceStamp" ]; then
	echo "ambient-canvas-player swift sources unchanged, skipping recompile" >&2
else
	echo "compiling ambient-canvas-player swift binary..." >&2
	mkdir -p "$(dirname "$AMBIENT_CANVAS_PLAYER_BINARY_PATH")"
	ambientCanvasPlayerSourceFiles=()
	while IFS= read -r -d "" ambientCanvasPlayerSourceFile; do
		ambientCanvasPlayerSourceFiles+=("$ambientCanvasPlayerSourceFile")
	done < <(/usr/bin/find "$AMBIENT_CANVAS_PLAYER_SOURCES_DIR" -name '*.swift' -print0)
	if /usr/bin/swiftc -O -o "$AMBIENT_CANVAS_PLAYER_BINARY_PATH" "${ambientCanvasPlayerSourceFiles[@]}"; then
		chmod 0755 "$AMBIENT_CANVAS_PLAYER_BINARY_PATH"
		printf '%s' "$ambientCanvasPlayerSourceStamp" >"$ambientCanvasPlayerSourceStampPath"
		/usr/bin/pkill -f "$AMBIENT_CANVAS_PLAYER_BINARY_PATH" 2>/dev/null || true
	else
		echo "ambient-canvas-player swift compile failed; leaving previous binary in place" >&2
	fi
fi
