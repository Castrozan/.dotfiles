#!/usr/bin/env bash
# Aligns macOS dark mode, desktop wallpaper, and accent color with the active
# theme. Driven by DESIRED_DARK_MODE, WALLPAPER_PATH, THEME_ACCENT_HEX, and
# ACCENT_FROM_HEX_SCRIPT env vars set by the home-manager activation wrapper.
# System Events can take >60s to respond during heavy nix-darwin activation,
# so each osascript is wrapped in `with timeout of 120 seconds` and stderr is
# silenced because failures are non-fatal (the script keeps moving).
# home-manager runs activation under `set -e`, where a failed command
# substitution in an assignment is fatal even with stderr silenced. A headless
# rebuild over SSH has no GUI session, so every System Events osascript exits
# non-zero; without `|| true` the GET assignments below abort the whole
# activation before later generations (home.file links, agent workspaces) run.

CURRENT_DARK_MODE=$(/usr/bin/osascript -e 'with timeout of 120 seconds' -e 'tell application "System Events" to tell appearance preferences to get dark mode' -e 'end timeout' 2>/dev/null || true)
if [ "$CURRENT_DARK_MODE" != "$DESIRED_DARK_MODE" ]; then
	/usr/bin/osascript -e 'with timeout of 120 seconds' -e 'tell application "System Events" to tell appearance preferences to set dark mode to '"$DESIRED_DARK_MODE" -e 'end timeout' 2>/dev/null || true
fi

CURRENT_WALLPAPER=$(/usr/bin/osascript -e 'with timeout of 120 seconds' -e 'tell application "System Events" to tell desktop 1 to get picture' -e 'end timeout' 2>/dev/null || true)
if [ "$CURRENT_WALLPAPER" != "$WALLPAPER_PATH" ]; then
	/usr/bin/osascript -e 'with timeout of 120 seconds' -e 'tell application "System Events" to tell every desktop to set picture to "'"$WALLPAPER_PATH"'"' -e 'end timeout' 2>/dev/null || true
fi

MACOS_ACCENT_COLOR=$(/usr/bin/python3 "$ACCENT_FROM_HEX_SCRIPT" "$THEME_ACCENT_HEX" || true)

CURRENT_ACCENT_COLOR=$(/usr/bin/defaults read -g AppleAccentColor 2>/dev/null || echo "4")
if [ "$MACOS_ACCENT_COLOR" != "$CURRENT_ACCENT_COLOR" ]; then
	if [ "$MACOS_ACCENT_COLOR" = "4" ]; then
		/usr/bin/defaults delete -g AppleAccentColor 2>/dev/null || true
	else
		/usr/bin/defaults write -g AppleAccentColor -int "$MACOS_ACCENT_COLOR" 2>/dev/null || true
	fi
fi
