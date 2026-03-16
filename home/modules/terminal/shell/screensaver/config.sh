#!/usr/bin/env bash

# shellcheck disable=SC2034

_resolve_primary_screensaver_command() {
	if command -v openclaw-mesh &>/dev/null; then
		echo 'openclaw-mesh'
	elif command -v cbonsai &>/dev/null; then
		echo 'cbonsai --live --infinite'
	else
		echo 'cmatrix -b -s'
	fi
}

SCREENSAVER_COMMANDS=(
	"$(_resolve_primary_screensaver_command)"
	'cmatrix -b'
	'sleep 3; bad-apple'
)
