#!/usr/bin/env bash

# shellcheck disable=SC2034

_resolve_primary_screensaver_command() {
	if command -v cbonsai &>/dev/null; then
		echo 'cbonsai --live --infinite'
	else
		echo 'cmatrix -b -s -u 8'
	fi
}

SCREENSAVER_COMMANDS=(
	"$(_resolve_primary_screensaver_command)"
	'cmatrix -b -u 8'
	'sleep 3; bad-apple'
)
