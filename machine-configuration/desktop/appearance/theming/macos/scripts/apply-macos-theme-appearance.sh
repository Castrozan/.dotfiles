#!/usr/bin/env bash
CURRENT_DARK_MODE=$(/usr/bin/osascript -e 'with timeout of 120 seconds' -e 'tell application "System Events" to tell appearance preferences to get dark mode' -e 'end timeout' 2>/dev/null || true)
if [ "$CURRENT_DARK_MODE" != "$DESIRED_DARK_MODE" ]; then
	/usr/bin/osascript -e 'with timeout of 120 seconds' -e 'tell application "System Events" to tell appearance preferences to set dark mode to '"$DESIRED_DARK_MODE" -e 'end timeout' 2>/dev/null || true
fi

CURRENT_WALLPAPER=$(/usr/bin/osascript -e 'with timeout of 120 seconds' -e 'tell application "System Events" to tell desktop 1 to get picture' -e 'end timeout' 2>/dev/null || true)
if [ "$CURRENT_WALLPAPER" != "$WALLPAPER_PATH" ]; then
	/usr/bin/osascript -e 'with timeout of 120 seconds' -e 'tell application "System Events" to tell every desktop to set picture to "'"$WALLPAPER_PATH"'"' -e 'end timeout' 2>/dev/null || true
fi

MACOS_ACCENT_COLOR=$(/usr/bin/python3 "$ACCENT_FROM_HEX_SCRIPT" "$THEME_ACCENT_HEX" || true)

CURRENT_ACCENT_COLOR=$("$TIMEOUT_BINARY_PATH" 5 /usr/bin/defaults read -g AppleAccentColor 2>/dev/null || echo "4")
if [ "$MACOS_ACCENT_COLOR" != "$CURRENT_ACCENT_COLOR" ]; then
	if [ "$MACOS_ACCENT_COLOR" = "4" ]; then
		"$TIMEOUT_BINARY_PATH" 5 /usr/bin/defaults delete -g AppleAccentColor 2>/dev/null || true
	else
		"$TIMEOUT_BINARY_PATH" 5 /usr/bin/defaults write -g AppleAccentColor -int "$MACOS_ACCENT_COLOR" 2>/dev/null || true
	fi
fi
