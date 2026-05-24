#!/usr/bin/env bash
# Initializes one discord-agent workspace dir at $1 with a HEARTBEAT.md and a
# .claude.json seed if either is missing. Reads the installed claude version
# from the binary at $2 (falls back to a known good version when unavailable).

workspace="$1"
claudeBinary="$2"

mkdir -p "$workspace"
if [ ! -f "$workspace/HEARTBEAT.md" ]; then
	printf '# Heartbeat\n\nNo active work.\n' >"$workspace/HEARTBEAT.md"
fi
CLAUDE_VERSION="$("$claudeBinary" --version 2>/dev/null | head -1 | grep -oE '[0-9.]+' | head -1 || echo '2.1.100')"
if [ ! -f "$workspace/.claude.json" ]; then
	printf '{"hasCompletedOnboarding":true,"numStartups":1,"installMethod":"native","lastOnboardingVersion":"%s"}\n' "$CLAUDE_VERSION" >"$workspace/.claude.json"
fi
