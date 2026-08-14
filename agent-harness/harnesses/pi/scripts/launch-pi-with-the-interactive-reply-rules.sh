#!/usr/bin/env bash
set -euo pipefail

piIsAnsweringAHumanAtTheKeyboard() {
	case "${1:-}" in
	install | remove | uninstall | update | list | config | auth)
		return 1
		;;
	esac

	local previousArgument=""
	local argument
	for argument in "$@"; do
		case "$argument" in
		-p | --print | --export | --list-models | -v | --version | -h | --help)
			return 1
			;;
		esac
		if [ "$previousArgument" = "--mode" ] && [ "$argument" != "text" ]; then
			return 1
		fi
		previousArgument="$argument"
	done

	return 0
}

if piIsAnsweringAHumanAtTheKeyboard "$@"; then
	export AGENT_INTERACTIVE_PREFERENCES_PATH="$PI_INTERACTIVE_REPLY_RULES_FILE"
	exec "$PI_UNWRAPPED_BINARY" \
		--append-system-prompt "$PI_INTERACTIVE_REPLY_RULES_FILE" \
		--extension "$PI_HUMAN_REPLY_GUARD_EXTENSION" \
		"$@"
fi

exec "$PI_UNWRAPPED_BINARY" "$@"
